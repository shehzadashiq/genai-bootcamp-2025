import logging
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi
import boto3
from .vector_store_service import VectorStoreService
from .language_service import LanguageService

logger = logging.getLogger(__name__)

class ListeningService:
    _instance = None
    _cache_dir = "transcript_cache"
    _vector_store = None
    _language_service = None
    _runtime = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ListeningService, cls).__new__(cls)
            cls._vector_store = VectorStoreService()
            cls._language_service = LanguageService()
            
            # Initialize AWS Bedrock client
            try:
                cls._runtime = boto3.client('bedrock-runtime')
                logger.info("Successfully initialized Bedrock runtime client")
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock runtime client: {e}")
                cls._runtime = None
            
            # Create cache directory if it doesn't exist
            if not os.path.exists(cls._cache_dir):
                os.makedirs(cls._cache_dir)
                
        return cls._instance
    
    def _get_cache_path(self, video_id: str) -> str:
        """Get path to cache file for video."""
        return os.path.join(self._cache_dir, f"{video_id}.json")
    
    def _read_cache(self, video_id: str) -> Optional[Dict]:
        """Read transcript from cache if available."""
        try:
            cache_path = self._get_cache_path(video_id)
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
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
    
    def get_transcript(self, video_id: str) -> List[Dict]:
        """
        Get transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of transcript segments with text converted to Urdu script
        """
        try:
            # Try to get from cache first
            cached_data = self._read_cache(video_id)
            if cached_data:
                return cached_data["transcript"]
            
            # Fetch transcript from YouTube
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get Urdu transcript first
            try:
                transcript = transcript_list.find_transcript(['ur'])
                logger.info("Found Urdu transcript")
            except:
                # If no Urdu transcript, try Hindi
                try:
                    transcript = transcript_list.find_transcript(['hi'])
                    logger.info("Found Hindi transcript")
                except:
                    # If no Hindi transcript, get any available transcript
                    transcript = transcript_list.find_transcript(['en'])
                    logger.info("Using fallback transcript")
            
            # Get transcript data
            transcript_data = transcript.fetch()
            
            # Convert Hindi text to Urdu if needed
            converted_data = []
            for segment in transcript_data:
                text = segment.get('text', '').strip()
                if not text:
                    continue
                    
                # Convert if not already in Urdu script
                if not any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text):
                    urdu_text = self._language_service.convert_hindi_to_urdu(text)
                    converted_data.append({**segment, 'text': urdu_text})
                else:
                    converted_data.append(segment)
            
            # Cache the converted transcript
            cache_data = {
                "video_id": video_id,
                "transcript": converted_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            self._write_cache(video_id, cache_data)
            
            # Add to vector store
            self._vector_store.add_transcript(video_id, converted_data)
            
            logger.info(f"Successfully processed transcript for video {video_id}")
            return converted_data
            
        except Exception as e:
            logger.error(f"Error getting transcript for video {video_id}: {e}")
            return []
    
    def prepare_for_vector_store(self, transcript: List[Dict], chunk_size: int = 100, overlap: int = 20) -> List[Dict]:
        """
        Prepare transcript chunks for vector store.
        
        Args:
            transcript: List of transcript segments
            chunk_size: Maximum number of characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of chunks with metadata
        """
        try:
            if not transcript:
                return []
            
            documents = []
            current_chunk = ""
            current_start = 0
            current_end = 0
            doc_id = 0
            
            for segment in transcript:
                text = segment.get('text', '').strip()
                if not text:
                    continue
                
                # Add segment to current chunk
                if current_chunk:
                    current_chunk += " "
                current_chunk += text
                
                # Update timing
                if not current_start:
                    current_start = segment.get('start', 0)
                current_end = segment.get('start', 0) + segment.get('duration', 0)
                
                # Check if chunk is full
                if len(current_chunk) >= chunk_size:
                    # Create document
                    documents.append({
                        'text': current_chunk,
                        'metadata': {
                            'start_time': current_start,
                            'end_time': current_end,
                            'language': segment.get('language', 'ur'),
                            'timestamp': datetime.utcnow().isoformat(),
                            'type': 'transcript_chunk'
                        }
                    })
                    doc_id += 1
                    
                    # Start new chunk with overlap
                    words = current_chunk.split()
                    overlap_text = ' '.join(words[-int(len(words)*overlap/chunk_size):])
                    current_chunk = overlap_text
                    current_start = current_end - 2  # Approximate overlap time
            
            # Add final chunk if not empty
            if current_chunk:
                documents.append({
                    'text': current_chunk,
                    'metadata': {
                        'start_time': current_start,
                        'end_time': current_end,
                        'language': transcript[-1].get('language', 'ur'),
                        'timestamp': datetime.utcnow().isoformat(),
                        'type': 'transcript_chunk'
                    }
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error preparing transcript chunks: {e}")
            return []
    
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

    def get_transcript_with_stats(self, video_url: str) -> Dict:
        """Get transcript and generate statistics."""
        try:
            # Extract video ID
            video_id = self.extract_video_id(video_url)
            if not video_id:
                return {
                    "error": "Invalid YouTube URL",
                    "transcript": [],
                    "statistics": self._empty_stats()
                }

            # Get transcript
            transcript = self.get_transcript(video_id)
            if not transcript:
                return {
                    "transcript": [],
                    "statistics": self._empty_stats()
                }

            # Convert Hindi text to Urdu
            converted_transcript = []
            for segment in transcript:
                text = segment.get('text', '').strip()
                # Convert if not already in Urdu script
                if text and not any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text):
                    urdu_text = self._language_service.convert_hindi_to_urdu(text)
                    converted_transcript.append({**segment, 'text': urdu_text})
                else:
                    converted_transcript.append(segment)

            # Store converted transcript
            self.store_transcript(video_id, converted_transcript)

            # Calculate statistics
            stats = self._calculate_stats(converted_transcript)

            return {
                "transcript": converted_transcript,
                "statistics": stats
            }

        except Exception as e:
            logger.error(f"Error getting transcript with stats: {e}")
            return {
                "error": str(e),
                "transcript": [],
                "statistics": self._empty_stats()
            }

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
