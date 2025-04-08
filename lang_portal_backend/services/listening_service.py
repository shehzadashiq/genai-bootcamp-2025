import logging
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import boto3
from .vector_store_service import VectorStoreService
from .language_service import LanguageService
from services.improved_question_generator import ImprovedQuestionGenerator
from config import guardrails_config
import asyncio
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class ListeningService:
    _instance = None
    _cache_dir = "transcript_cache"
    _vector_store = None
    _language_service = None
    _question_generator = None
    _runtime = None
    
    def __init__(self):
        """Initialize the listening service."""
        self._cache_dir = "transcript_cache"
        # Create cache directory if it doesn't exist
        os.makedirs(self._cache_dir, exist_ok=True)
        self._language_service = LanguageService()
        self._question_generator = ImprovedQuestionGenerator()
        
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ListeningService, cls).__new__(cls)
            cls._vector_store = VectorStoreService()
            
            # Initialize AWS Bedrock client
            try:
                cls._runtime = boto3.client('bedrock-runtime')
                logger.info("Successfully initialized Bedrock runtime client")
            except Exception as e:
                logger.error(f"Failed to initialize Bedrock runtime client: {e}")
                cls._runtime = None
            
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
    
    def get_transcript(self, video_url: str) -> List[Dict]:
        """Get transcript for a YouTube video."""
        try:
            # Extract video ID first
            video_id = self.extract_video_id(video_url)
            if not video_id:
                logger.error(f"Could not extract video ID from URL: {video_url}")
                return []

            logger.info(f"Getting transcript for video ID: {video_id}")
            
            # Try to get from cache first
            cached_data = self._read_cache(video_id)
            if cached_data:
                logger.info(f"Using cached transcript for video {video_id}")
                return cached_data["transcript"]
            
            # Fetch transcript list from YouTube using video ID
            try:
                logger.info(f"Fetching transcript list for video ID: {video_id}")
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Log available languages
                manual_langs = [t.language_code for t in transcript_list._manually_created_transcripts.values()]
                auto_langs = [t.language_code for t in transcript_list._generated_transcripts.values()]
                logger.info(f"Available manual transcripts: {manual_langs}")
                logger.info(f"Available auto-generated transcripts: {auto_langs}")
                
                # Try to get English transcript first
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    logger.info(f"Found English transcript for video {video_id}")
                except NoTranscriptFound:
                    # If no English transcript, try to get any transcript and translate it
                    logger.info(f"No English transcript found, getting any available transcript")
                    transcript = transcript_list.find_transcript(['ur', 'hi', 'en'])
                    if transcript.language_code != 'en':
                        logger.info(f"Translating transcript from {transcript.language_code} to English")
                        transcript = transcript.translate('en')
                
                # Fetch the actual transcript data
                transcript_data = transcript.fetch()
                logger.info(f"Fetched transcript data: {len(transcript_data)} segments")
                
                # Cache the transcript
                self._write_cache(video_id, {"transcript": transcript_data})
                
                return transcript_data
                
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                logger.error(f"No transcripts available for video {video_id}: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
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

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        logger.info(f"Extracting video ID from URL: {url}")
        
        try:
            # Handle empty URL
            if not url:
                logger.error("Empty URL provided")
                return None
                
            # If it's already just the video ID (11 characters)
            if re.match(r'^[A-Za-z0-9_-]{11}$', url):
                logger.info(f"URL is already a video ID: {url}")
                return url
                
            # Clean up the URL first
            url = url.strip()
            if url.endswith('&'):
                url = url[:-1]
                
            # Try to parse URL
            parsed_url = urlparse(url)
            logger.debug(f"Parsed URL - netloc: {parsed_url.netloc}, path: {parsed_url.path}, query: {parsed_url.query}")
            
            # Handle youtube.com URLs
            if 'youtube.com' in parsed_url.netloc:
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    video_id = query_params['v'][0]
                    # Clean up video ID
                    video_id = video_id.split('&')[0]
                    logger.info(f"Found video ID in query params: {video_id}")
                    return video_id
                    
            # Handle youtu.be URLs
            elif 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.strip('/')
                # Clean up video ID
                video_id = video_id.split('&')[0]
                logger.info(f"Found video ID in youtu.be path: {video_id}")
                return video_id
                
            # Try regex patterns as fallback
            patterns = [
                r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})',
                r'youtube\.com\/watch\?.*v=([^"&?\/\s]{11})',
                r'youtube\.com\/embed\/([^"&?\/\s]{11})',
                r'youtube\.com\/v\/([^"&?\/\s]{11})',
                r'youtu\.be\/([^"&?\/\s]{11})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    logger.info(f"Found video ID using regex: {video_id}")
                    return video_id
                    
            logger.error(f"Could not extract video ID from URL: {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting video ID: {e}")
            return None

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
                transcript = self.get_transcript(video_url)
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
                    urdu_segments.append({
                        'text': text,
                        'start': segment.get('start', 0),
                        'duration': segment.get('duration', 0)
                    })
            
            if not urdu_segments:
                logger.error("No valid Urdu segments found")
                return []
                
            # Combine segments into a single text for context
            full_text = " ".join(segment['text'] for segment in urdu_segments)
            
            # Generate questions using the improved question generator
            # Create new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            questions = loop.run_until_complete(
                self._question_generator.generate_questions(
                    text=full_text,
                    num_questions=num_questions,
                    language='ur'
                )
            )
            
            # Add audio timestamps to questions
            for question in questions:
                # Find relevant segment for this question
                for segment in urdu_segments:
                    if any(word in segment['text'] for word in question['question'].split()):
                        question['audio_start'] = segment['start']
                        question['audio_end'] = segment['start'] + segment['duration']
                        break
            
            return questions

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []

    def store_transcript(self, video_url: str, transcript: List[Dict]) -> bool:
        """Store transcript in cache."""
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                logger.error("Invalid video URL")
                return False
                
            data = {
                "video_id": video_id,
                "transcript": transcript,
                "timestamp": datetime.now().isoformat()
            }
            return self._write_cache(video_id, data)
        except Exception as e:
            logger.error(f"Error writing cache for video {video_url}: {e}")
            return False

    def get_transcript_with_stats(self, video_url: str) -> Dict:
        """Get transcript and generate statistics."""
        try:
            video_id = self.extract_video_id(video_url)
            if not video_id:
                return {
                    "error": "Invalid YouTube URL",
                    "transcript": None,
                    "statistics": self._empty_stats()
                }

            # Get transcript
            transcript = self.get_transcript(video_url)
            if not transcript:
                return {
                    "error": "No transcript available for this video",
                    "transcript": None,
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
            self.store_transcript(video_url, converted_transcript)

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
                "transcript": None,
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
