"""
Listening Service for handling YouTube transcripts and vector storage.
Integrates with VectorStoreService for robust semantic search capabilities.
"""
import logging
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Union, Tuple, Any
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import boto3
from .vector_store_service import VectorStoreService
from .language_service import LanguageService
from config import guardrails_config, vector_store_config, aws_config

logger = logging.getLogger(__name__)

class ListeningService:
    _instance = None
    _cache_dir = "transcript_cache"
    _vector_store = None
    _language_service = None
    _runtime = None
    _questions_collection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ListeningService, cls).__new__(cls)
            try:
                # Initialize services
                cls._vector_store = VectorStoreService()
                cls._language_service = LanguageService()
                
                # Initialize AWS Bedrock client with proper configuration
                cls._runtime = boto3.client(
                    'bedrock-runtime',
                    region_name=aws_config.AWS_REGION,
                    aws_access_key_id=aws_config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=aws_config.AWS_SECRET_ACCESS_KEY
                )
                
                # Verify required permissions
                try:
                    # Test Bedrock model access
                    cls._runtime.invoke_model(
                        modelId=aws_config.BEDROCK_MODEL_ID,
                        contentType="application/json",
                        accept="application/json",
                        body=json.dumps({
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 10,
                            "messages": [{"role": "user", "content": [{"type": "text", "text": "test"}]}]
                        }).encode()
                    )
                    logger.info("Successfully verified Bedrock model access")
                except Exception as e:
                    logger.error(f"Failed to verify Bedrock model access: {e}")
                    raise ValueError(
                        "Missing required AWS permissions. Please ensure the following IAM permissions are granted: " + 
                        ", ".join(aws_config.REQUIRED_PERMISSIONS)
                    )
                
                # Create cache directory if it doesn't exist
                cache_dir = os.path.abspath(cls._cache_dir)
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir)
                    
            except Exception as e:
                logger.error(f"Failed to initialize services: {e}")
                raise
                
        return cls._instance
    
    def __init__(self, runtime: Any = None, vector_store: Any = None):
        """Initialize the service with AWS runtime and vector store."""
        # Initialize AWS Bedrock client
        self._runtime = runtime or boto3.client(
            'bedrock-runtime',
            aws_access_key_id=aws_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=aws_config.AWS_SECRET_ACCESS_KEY,
            region_name=aws_config.AWS_REGION
        )
        
        # Initialize vector store if not provided
        if vector_store is None:
            try:
                import chromadb
                from chromadb.config import Settings
                from chromadb.utils import embedding_functions
                
                # Create Bedrock embedding function
                bedrock_ef = embedding_functions.BedrockEmbeddingFunction(
                    aws_access_key_id=aws_config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=aws_config.AWS_SECRET_ACCESS_KEY,
                    region_name=aws_config.AWS_REGION,
                    model_id=aws_config.VECTOR_STORE_EMBEDDING_MODEL
                )
                
                # Initialize ChromaDB with persistent storage
                self._vector_store = chromadb.Client(
                    Settings(
                        persist_directory="./chroma_db",
                        anonymized_telemetry=False
                    )
                )
                
                # Create or get questions collection
                try:
                    self._questions_collection = self._vector_store.create_collection(
                        name=aws_config.VECTOR_STORE_COLLECTION_NAME,
                        embedding_function=bedrock_ef,
                        metadata={"hnsw:space": "cosine"}
                    )
                except ValueError:  # Collection already exists
                    self._questions_collection = self._vector_store.get_collection(
                        name=aws_config.VECTOR_STORE_COLLECTION_NAME,
                        embedding_function=bedrock_ef
                    )
                    
                logger.info("Successfully initialized ChromaDB with Bedrock embeddings")
                
            except ImportError:
                logger.warning("ChromaDB not installed, vector search disabled")
                self._vector_store = None
                self._questions_collection = None
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {e}")
                self._vector_store = None
                self._questions_collection = None
        else:
            self._vector_store = vector_store
            try:
                self._questions_collection = self._vector_store.get_collection(
                    aws_config.VECTOR_STORE_COLLECTION_NAME
                )
            except Exception as e:
                logger.error(f"Failed to get questions collection: {e}")
                self._questions_collection = None
    
    def _get_cache_path(self, video_id: str) -> str:
        """Get path to cache file for video."""
        cache_dir = os.path.abspath(self._cache_dir)
        return os.path.join(cache_dir, f"{video_id}.json")
    
    def _read_cache(self, video_id: str) -> Optional[Dict]:
        """Read transcript from cache if available."""
        try:
            cache_path = self._get_cache_path(video_id)
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Validate cache data
                    if not isinstance(data, dict) or 'transcript' not in data:
                        logger.warning(f"Invalid cache data for video {video_id}")
                        return None
                    return data
        except Exception as e:
            logger.error(f"Error reading cache for video {video_id}: {e}")
        return None
    
    def _write_cache(self, video_id: str, data: Dict) -> bool:
        """Write transcript data to cache."""
        try:
            cache_path = self._get_cache_path(video_id)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing cache for video {video_id}: {e}")
            return False

    def extract_video_id(self, url_or_id: str) -> str:
        """Extract video ID from URL or return the ID if already in correct format."""
        if not url_or_id:
            raise ValueError("URL or video ID is required")
            
        # Clean input
        url_or_id = url_or_id.strip()
        
        # If it's already an 11-character ID, validate and return it
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            return url_or_id
        
        # Try to extract from various URL formats
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch.*?v=([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url_or_id)
            if match:
                video_id = match.group(1)
                if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
                    return video_id
        
        raise ValueError("Invalid YouTube URL or video ID format")
        
    def get_transcript(self, video_id: str) -> List[Dict[str, Any]]:
        """Get transcript for a video, process it, and store in vector store."""
        try:
            # Validate video ID
            video_id = self.extract_video_id(video_id)
            
            # Check cache first
            cached_data = self._read_cache(video_id)
            if cached_data:
                logger.info(f"Using cached transcript for video {video_id}")
                return cached_data['transcript']
            
            # Get transcript list
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            logger.info(f"Retrieved transcript list for video {video_id}")
            
            # Try to get transcript in preferred order: manual Hindi -> auto Hindi -> manual English -> auto English
            transcript = None
            try:
                # Try manual Hindi first
                transcript = transcript_list.find_manually_created_transcript(['hi'])
                logger.info("Found manual Hindi transcript")
            except:
                try:
                    # Try auto-generated Hindi
                    transcript = transcript_list.find_generated_transcript(['hi'])
                    logger.info("Found auto-generated Hindi transcript")
                except:
                    try:
                        # Try manual English
                        transcript = transcript_list.find_manually_created_transcript(['en'])
                        logger.info("Found manual English transcript")
                    except:
                        try:
                            # Try auto-generated English
                            transcript = transcript_list.find_generated_transcript(['en'])
                            logger.info("Found auto-generated English transcript")
                        except Exception as e:
                            logger.error(f"No suitable transcript found: {str(e)}")
                            # List available languages for debugging
                            manual_langs = [f"{lang.language_code} ({lang.language})" for lang in transcript_list._manually_created_transcripts.values()]
                            auto_langs = [f"{lang.language_code} ({lang.language})" for lang in transcript_list._generated_transcripts.values()]
                            logger.info(f"Available manual transcripts: {manual_langs}")
                            logger.info(f"Available auto transcripts: {auto_langs}")
                            raise ValueError("No Hindi or English transcript available for this video")
            
            # Fetch transcript data
            transcript_data = transcript.fetch()
            logger.info(f"Fetched transcript data with {len(transcript_data)} segments")
            
            # Process each segment
            processed_segments = []
            for segment in transcript_data:
                text = segment.get('text', '').strip()
                if not text:
                    continue
                    
                # Convert to Urdu if needed
                translated_text, was_translated = self._language_service.convert_hindi_to_urdu(text)
                
                # Create segment with metadata
                processed_segment = {
                    'text': translated_text,
                    'original_text': text,
                    'start': segment.get('start', 0),
                    'duration': segment.get('duration', 0),
                    'source_language': transcript.language_code,
                    'language': 'ur' if was_translated else transcript.language_code,
                    'has_translation': was_translated
                }
                processed_segments.append(processed_segment)
                
                # Log segment processing
                if was_translated:
                    logger.info(f"Processed segment with translation: {text} -> {translated_text}")
                else:
                    logger.debug(f"Processed segment without translation: {text}")
            
            # Store in vector store if needed
            if self._vector_store and processed_segments:
                self._add_to_vector_store(video_id, processed_segments)
            
            # Cache the processed transcript
            cache_data = {
                'transcript': processed_segments,
                'metadata': {
                    'video_id': video_id,
                    'segments': len(processed_segments),
                    'languages': list(set(seg['language'] for seg in processed_segments)),
                    'has_translations': any(seg['has_translation'] for seg in processed_segments),
                    'cached_at': datetime.now().isoformat()
                }
            }
            self._write_cache(video_id, cache_data)
            
            return processed_segments
            
        except Exception as e:
            logger.error(f"Error getting transcript for video {video_id}: {str(e)}")
            raise

    def prepare_for_vector_store(self, transcript: List[Dict], chunk_size: int = 100, overlap: int = 20) -> List[Dict]:
        """Prepare transcript segments for vector store by chunking and adding metadata."""
        chunks = []
        current_chunk = []
        current_length = 0
        
        for segment in transcript:
            # Use the translated text if available
            text = segment['text']
            if not text:
                continue
                
            # Add segment to current chunk
            current_chunk.append({
                'text': text,
                'start': segment['start'],
                'duration': segment['duration'],
                'language': segment['language']
            })
            current_length += len(text.split())
            
            # If chunk is full, process it
            if current_length >= chunk_size:
                # Create chunk document
                chunk_text = ' '.join(seg['text'] for seg in current_chunk)
                chunk_start = current_chunk[0]['start']
                chunk_end = current_chunk[-1]['start'] + current_chunk[-1]['duration']
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'start_time': chunk_start,
                        'end_time': chunk_end,
                        'duration': chunk_end - chunk_start,
                        'language': current_chunk[0]['language']
                    }
                })
                
                # Keep overlap segments for next chunk
                overlap_segments = current_chunk[-overlap:] if overlap > 0 else []
                current_chunk = overlap_segments
                current_length = sum(len(seg['text'].split()) for seg in overlap_segments)
        
        # Add remaining segments as final chunk if any
        if current_chunk:
            chunk_text = ' '.join(seg['text'] for seg in current_chunk)
            chunk_start = current_chunk[0]['start']
            chunk_end = current_chunk[-1]['start'] + current_chunk[-1]['duration']
            
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'start_time': chunk_start,
                    'end_time': chunk_end,
                    'duration': chunk_end - chunk_start,
                    'language': current_chunk[0]['language']
                }
            })
        
        return chunks
        
    def _add_to_vector_store(self, video_id: str, transcript: List[Dict]) -> None:
        """Add transcript chunks to vector store with proper metadata."""
        try:
            # Prepare chunks for vector store
            chunks = self.prepare_for_vector_store(transcript)
            
            # Add chunks to vector store
            if self._vector_store:
                for chunk in chunks:
                    self._vector_store.add_document(
                        document=chunk['text'],
                        metadata={
                            'video_id': video_id,
                            **chunk['metadata']
                        }
                    )
                logger.info(f"Added {len(chunks)} chunks to vector store for video {video_id}")
            else:
                logger.warning("Vector store not initialized, skipping vector store addition")
                
        except Exception as e:
            logger.error(f"Error adding transcript to vector store: {str(e)}")
            # Don't raise the error since vector store is optional

    def convert_hindi_to_urdu(self, text: str) -> str:
        """Convert Hindi text to Urdu script."""
        return self._language_service.convert_hindi_to_urdu(text)

    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from various URL formats."""
        try:
            # Handle empty or invalid URLs
            if not url:
                logger.error("Empty URL provided")
                return ""

            # Common YouTube URL patterns
            patterns = [
                r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and shortened URLs
                r'(?:embed\/)([0-9A-Za-z_-]{11})',   # Embed URLs
                r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'  # Short URLs
            ]
            
            # Try each pattern
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    logger.info(f"Successfully extracted video ID: {video_id}")
                    return video_id
            
            # If no pattern matches, check if the URL itself is an ID
            if len(url) == 11 and all(c in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_-' for c in url):
                logger.info(f"URL appears to be a video ID: {url}")
                return url
            
            logger.warning(f"Could not extract video ID from URL: {url}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting video ID: {e}")
            return ""

    def get_questions_for_video(self, video_url: str) -> Dict:
        """Get transcript and generate questions for a video."""
        try:
            # Extract video ID
            video_id = self.extract_video_id(video_url)
            if not video_id:
                logger.error("Invalid YouTube URL")
                return {"error": "Invalid YouTube URL"}

            # Get transcript
            try:
                transcript = self.get_transcript(video_id)
                if not transcript:
                    logger.error("No transcript available")
                    return {"error": "No transcript available for this video"}
                logger.info(f"Got transcript with {len(transcript)} segments")
            except Exception as e:
                logger.error(f"Error getting transcript: {e}")
                return {"error": str(e)}

            # Generate questions
            try:
                questions = self._generate_questions(transcript)
                if not questions:
                    logger.error("No questions were generated")
                    return {"error": "Failed to generate questions"}
                
                logger.info(f"Generated {len(questions)} questions")
                return {"questions": questions}
                
            except Exception as e:
                logger.error(f"Error generating questions: {e}")
                return {"error": f"Failed to generate questions: {str(e)}"}

        except Exception as e:
            logger.error(f"Error in get_questions_for_video: {e}")
            return {"error": str(e)}

    def _generate_questions(self, transcript: List[Dict], num_questions: int = 5) -> List[Dict]:
        """Generate multiple-choice questions from transcript segments."""
        try:
            # Extract segments with Urdu text
            urdu_segments = []
            for segment in transcript:
                text = segment.get('text', '').strip()
                # Convert Hindi text to Urdu if needed
                if not any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text):
                    text = self._language_service.convert_hindi_to_urdu(text)
                if text:  # Only add if we have valid text
                    urdu_segments.append({**segment, 'text': text})
            
            if not urdu_segments:
                logger.warning("No Urdu segments found")
                return []

            # Select segments for questions
            selected_segments = urdu_segments[:num_questions]
            questions = []

            # Common wrong answers in Urdu
            wrong_answers = [
                "مجھے سمجھ نہیں آیا",  # "I didn't understand"
                "کچھ اور کہا گیا تھا",  # "Something else was said"
                "یہ متن دستیاب نہیں ہے",  # "This text is not available"
                "معلوم نہیں",  # "Don't know"
                "کوئی جواب نہیں",  # "No answer"
                "سن نہیں سکا",  # "Couldn't hear"
                "دوبارہ سنیں",  # "Listen again"
                "واضح نہیں ہے"  # "Not clear"
            ]

            for i, segment in enumerate(selected_segments):
                text = segment['text'].strip()
                start_time = segment.get('start', 0)
                duration = segment.get('duration', 0)
                
                # Create question with better Urdu phrasing
                question = {
                    "id": i + 1,
                    "question": "اس آڈیو حصے میں کیا کہا گیا ہے؟",  # "What was said in this audio segment?"
                    "options": [
                        text  # Correct answer is always first
                    ],
                    "correct_answer": text,
                    "audio_start": start_time,
                    "audio_end": start_time + duration
                }
                
                # Add 3 random wrong answers
                from random import sample
                question['options'].extend(sample(wrong_answers, 3))
                
                # Shuffle all options
                from random import shuffle
                correct = question['options'][0]
                shuffle(question['options'])
                # Update correct_answer to match shuffled position
                question['correct_answer'] = correct

                questions.append(question)

            return questions

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []

    def store_transcript(self, video_id: str, transcript: List[Dict]) -> bool:
        """Store transcript in cache and vector store."""
        try:
            # Store in cache
            cache_data = {
                "video_id": video_id,
                "transcript": transcript,
                "timestamp": datetime.utcnow().isoformat()
            }
            if not self._write_cache(video_id, cache_data):
                logger.error("Failed to write transcript to cache")
                return False

            # Store in vector store
            if not self._vector_store.add_transcript(video_id, transcript):
                logger.error("Failed to add transcript to vector store")
                return False

            logger.info(f"Successfully stored transcript for video {video_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing transcript: {e}")
            return False

    def get_transcript_with_stats(self, video_id: str) -> Dict[str, Any]:
        """Get transcript with additional statistics."""
        try:
            # Get transcript
            transcript = self.get_transcript(video_id)
            
            # Calculate statistics
            total_segments = len(transcript)
            total_duration = sum(seg['duration'] for seg in transcript)
            translated_segments = sum(1 for seg in transcript if seg['has_translation'])
            
            # Group segments by language
            language_stats = {}
            for seg in transcript:
                lang = seg['language']
                if lang not in language_stats:
                    language_stats[lang] = {
                        'count': 0,
                        'duration': 0,
                        'sample_text': []
                    }
                language_stats[lang]['count'] += 1
                language_stats[lang]['duration'] += seg['duration']
                if len(language_stats[lang]['sample_text']) < 3:  # Keep up to 3 samples
                    language_stats[lang]['sample_text'].append(seg['text'])
            
            # Format duration as MM:SS
            def format_duration(seconds):
                minutes = int(seconds // 60)
                seconds = int(seconds % 60)
                return f"{minutes:02d}:{seconds:02d}"
            
            # Prepare response
            return {
                'transcript': transcript,
                'stats': {
                    'total_segments': total_segments,
                    'total_duration': format_duration(total_duration),
                    'total_duration_seconds': total_duration,
                    'translated_segments': translated_segments,
                    'translation_percentage': round((translated_segments / total_segments * 100) if total_segments > 0 else 0, 1),
                    'languages': {
                        lang: {
                            'count': stats['count'],
                            'duration': format_duration(stats['duration']),
                            'percentage': round((stats['count'] / total_segments * 100) if total_segments > 0 else 0, 1),
                            'sample_text': stats['sample_text']
                        }
                        for lang, stats in language_stats.items()
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting transcript with stats: {str(e)}")
            raise

    def _empty_stats(self) -> Dict:
        """Return empty statistics structure."""
        return {
            "total_duration": 0,
            "total_words": 0,
            "avg_words_per_minute": 0,
            "segments_count": 0,
            "urdu_segments_count": 0,
            "hindi_segments_count": 0,
            "top_words": {}
        }

    def _calculate_stats(self, transcript: List[Dict]) -> Dict:
        """Calculate transcript statistics."""
        try:
            if not transcript:
                return self._empty_stats()

            # Basic stats
            total_duration = sum(segment.get('duration', 0) for segment in transcript)
            total_words = 0
            urdu_segments = 0
            hindi_segments = 0
            word_freq = {}

            # Process each segment
            for segment in transcript:
                text = segment.get('text', '').strip()
                if not text:
                    continue

                # Count words and update frequency
                words = text.split()
                total_words += len(words)
                for word in words:
                    word = word.strip('.,!?()[]{}":;')
                    if word:
                        word_freq[word] = word_freq.get(word, 0) + 1

                # Detect script
                if any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text):
                    urdu_segments += 1
                elif any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in text):
                    hindi_segments += 1

            # Calculate words per minute
            avg_words_per_minute = (total_words / total_duration) * 60 if total_duration > 0 else 0

            # Get top words (limit to 10)
            top_words = dict(sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10])

            return {
                "total_duration": round(total_duration, 2),
                "total_words": total_words,
                "avg_words_per_minute": round(avg_words_per_minute, 2),
                "segments_count": len(transcript),
                "urdu_segments_count": urdu_segments,
                "hindi_segments_count": hindi_segments,
                "top_words": top_words
            }

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return self._empty_stats()

    def get_questions(self, video_id: str) -> List[Dict[str, Any]]:
        """Generate questions for a video using AWS Bedrock and vector similarity search."""
        try:
            # Get transcript first
            transcript = self.get_transcript(video_id)
            if not transcript:
                raise ValueError("No transcript available")

            # Combine transcript segments into a single text
            combined_text = " ".join(seg["text"] for seg in transcript)
            if not combined_text.strip():
                raise ValueError("Empty transcript text")

            # Try vector search only if collection is initialized
            if self._questions_collection is not None:
                try:
                    # Query similar questions using ChromaDB with Titan embeddings
                    results = self._questions_collection.query(
                        query_texts=[combined_text],
                        n_results=5,
                        where={"video_id": video_id},
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    # Check if we found good matches
                    if (results and 
                        results["documents"] and 
                        results["distances"] and 
                        results["distances"][0][0] <= (1 - aws_config.VECTOR_STORE_SIMILARITY_THRESHOLD)):
                        
                        logger.info(f"Found similar questions for video {video_id} with similarity {1 - results['distances'][0][0]:.2f}")
                        return json.loads(results["documents"][0][0])
                        
                except Exception as e:
                    logger.warning(f"Error searching for similar questions: {e}")
            else:
                logger.info("Vector store not available, proceeding with question generation")

            # Generate new questions using Bedrock Claude
            prompt = {
                "prompt": "\n\nHuman: " + aws_config.QUESTION_GENERATION_PROMPT.format(
                    text=combined_text[:2000]  # Limit transcript length
                ) + "\n\nAssistant: ",
                "max_tokens_to_sample": aws_config.BEDROCK_MAX_TOKENS,
                "temperature": aws_config.BEDROCK_TEMPERATURE,
                "top_p": aws_config.BEDROCK_TOP_P,
                "stop_sequences": ["\n\nHuman:"]
            }

            # Call Bedrock with proper error handling
            try:
                response = self._runtime.invoke_model(
                    modelId=aws_config.BEDROCK_MODEL_ID,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(prompt).encode()
                )
                
                # Parse response
                response_body = json.loads(response.get('body').read())
                if not response_body:
                    raise ValueError("Empty response from Bedrock")
                    
                # Get completion from response
                completion = response_body.get('completion')
                if not completion:
                    raise ValueError("No completion in model response")
                
                # Clean up completion text
                completion = completion.strip()
                if not completion:
                    raise ValueError("Empty completion text")
                
                # Try to find JSON array in response
                try:
                    # First try direct JSON parsing
                    questions = json.loads(completion)
                except json.JSONDecodeError:
                    # If that fails, try to find JSON array in text
                    json_match = re.search(r'\[.*\]', completion, re.DOTALL)
                    if not json_match:
                        raise ValueError("No JSON array found in response")
                    try:
                        questions = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        raise ValueError("Invalid JSON format in response")
                
                if not isinstance(questions, list) or not questions:
                    raise ValueError("Invalid questions format")
                
                # Validate each question
                for i, question in enumerate(questions):
                    if not isinstance(question, dict):
                        raise ValueError(f"Question {i} is not a dictionary")
                        
                    # Check required fields
                    missing_fields = []
                    for field in ['question', 'options', 'correct_answer']:
                        if field not in question:
                            missing_fields.append(field)
                    if missing_fields:
                        raise ValueError(f"Question {i} missing fields: {', '.join(missing_fields)}")
                    
                    # Validate options
                    if not isinstance(question['options'], list):
                        raise ValueError(f"Question {i} options is not a list")
                    if len(question['options']) != 4:
                        raise ValueError(f"Question {i} must have exactly 4 options")
                    
                    # Validate option prefixes
                    invalid_options = []
                    for j, opt in enumerate(question['options']):
                        if not isinstance(opt, str):
                            invalid_options.append(f"Option {j} is not a string")
                        elif not opt.startswith(('A. ', 'B. ', 'C. ', 'D. ')):
                            invalid_options.append(f"Option {j} does not start with A./B./C./D.")
                    if invalid_options:
                        raise ValueError(f"Question {i} has invalid options: {', '.join(invalid_options)}")
                    
                    # Validate correct answer
                    if not isinstance(question['correct_answer'], str):
                        raise ValueError(f"Question {i} correct_answer is not a string")
                    if question['correct_answer'] not in question['options']:
                        raise ValueError(f"Question {i} correct_answer not in options")
                
                # Store in vector store if available
                if self._questions_collection is not None:
                    try:
                        # Store questions as JSON string with Titan embeddings
                        self._questions_collection.add(
                            documents=[json.dumps(questions)],
                            metadatas=[{
                                "video_id": video_id,
                                "generated_at": datetime.now().isoformat(),
                                "source": "bedrock",
                                "model": aws_config.BEDROCK_MODEL_ID,
                                "embedding_model": aws_config.VECTOR_STORE_EMBEDDING_MODEL,
                                "embedding_dim": aws_config.VECTOR_STORE_EMBEDDING_DIM
                            }],
                            ids=[f"{video_id}_{datetime.now().timestamp()}"]
                        )
                        logger.info(f"Stored questions in vector store for video {video_id}")
                    except Exception as e:
                        logger.warning(f"Failed to store questions in vector store: {e}")
                
                logger.info(f"Successfully generated {len(questions)} questions for video {video_id}")
                return questions
                
            except self._runtime.exceptions.ValidationException as e:
                logger.error(f"Bedrock validation error: {e}")
                raise ValueError("Invalid request format")
            except self._runtime.exceptions.ModelNotReadyException as e:
                logger.error(f"Bedrock model not ready: {e}")
                raise ValueError("Service temporarily unavailable")
            except self._runtime.exceptions.ThrottlingException as e:
                logger.error(f"Bedrock throttling error: {e}")
                raise ValueError("Rate limit exceeded")
            except (json.JSONDecodeError, KeyError, IndexError) as e:
                logger.error(f"Error processing Bedrock response: {e}")
                raise ValueError("Failed to process generated questions")
                
        except Exception as e:
            logger.error(f"Error in question generation: {e}")
            raise ValueError(f"Failed to generate questions: {e}")
