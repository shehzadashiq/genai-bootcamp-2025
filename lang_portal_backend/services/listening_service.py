from youtube_transcript_api import YouTubeTranscriptApi
import os
from typing import List, Dict, Optional, Tuple
import re
from collections import Counter
import json
import boto3
import botocore.config
import logging
import hashlib
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ListeningService:
    _instance = None
    _bedrock = None
    _runtime = None
    
    # Hindi to Urdu script mapping
    _script_map = {
        # Vowels
        'अ': 'ا', 'आ': 'آ', 'इ': 'ا', 'ई': 'ی',
        'उ': 'ا', 'ऊ': 'و', 'ए': 'ے', 'ऐ': 'ے',
        'ओ': 'و', 'औ': 'و', 'ं': 'ں', 'ः': '',
        
        # Consonants
        'क': 'ک', 'ख': 'کھ', 'ग': 'گ', 'घ': 'گھ', 'ङ': 'نگ',
        'च': 'چ', 'छ': 'چھ', 'ज': 'ج', 'झ': 'جھ', 'ञ': 'نج',
        'ट': 'ٹ', 'ठ': 'ٹھ', 'ड': 'ڈ', 'ढ': 'ڈھ', 'ण': 'ن',
        'त': 'ت', 'थ': 'تھ', 'द': 'د', 'ध': 'دھ', 'न': 'ن',
        'प': 'پ', 'फ': 'फ', 'ब': 'ب', 'भ': 'بھ', 'म': 'م',
        'य': 'ی', 'र': 'ر', 'ल': 'ل', 'व': 'و',
        'श': 'ش', 'ष': 'श', 'स': 'س', 'ह': 'ہ',
        
        # Matras (vowel signs)
        'ा': 'ا', 'ि': '', 'ी': 'ی',
        'ु': '', 'ू': 'व', 'े': 'ے',
        'ै': 'ے', 'ो': 'व', 'ौ': 'व',
        '्': '',  # Halant
        
        # Numerals
        '०': '०', '१': '१', '२': '२', '३': '३', '४': '४',
        '५': '५', '६': '६', '७': '७', '८': '८', '९': '९',
        
        # Punctuation
        '।': '۔', '॥': '۔',
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ListeningService, cls).__new__(cls)
            
            # Initialize AWS Bedrock client
            try:
                logger.info("Initializing AWS Bedrock client...")
                config = botocore.config.Config(
                    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                    retries={'max_attempts': 3}
                )
                cls._bedrock = boto3.client(
                    'bedrock', 
                    config=config,
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
                cls._runtime = boto3.client(
                    'bedrock-runtime', 
                    config=config,
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
                logger.info("AWS Bedrock client initialized successfully")
            except Exception as e:
                logger.error(f"AWS Bedrock initialization failed: {e}")
                cls._bedrock = None
                cls._runtime = None
                
        return cls._instance

    def __init__(self):
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache', 'transcripts')
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, video_id: str) -> str:
        """Generate a cache file path for a video ID."""
        return os.path.join(self.cache_dir, f"{video_id}.json")

    def _cache_exists(self, video_id: str) -> bool:
        """Check if cache exists for a video ID."""
        cache_path = self._get_cache_path(video_id)
        return os.path.exists(cache_path)

    def _read_cache(self, video_id: str) -> Optional[Dict]:
        """Read cached transcript data."""
        try:
            cache_path = self._get_cache_path(video_id)
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading cache for video {video_id}: {e}")
        return None

    def _write_cache(self, video_id: str, data: Dict) -> None:
        """Write transcript data to cache."""
        try:
            cache_path = self._get_cache_path(video_id)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error writing cache for video {video_id}: {e}")

    def extract_video_id(self, url: str) -> str:
        """Extract YouTube video ID from various URL formats."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and shortened URLs
            r'(?:embed\/)([0-9A-Za-z_-]{11})',   # Embed URLs
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'  # Short URLs
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return url  # Return as is if no pattern matches

    def get_transcript(self, video_id: str) -> List[Dict]:
        """Get transcript for a YouTube video with language priority."""
        try:
            # Try to get from cache first
            cached_data = self._read_cache(video_id)
            if cached_data:
                logger.info(f"Using cached transcript for video {video_id}")
                return cached_data["transcript"]

            # If not in cache, get the transcript list
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            final_transcript = None
            
            # Try to get Urdu transcript first
            try:
                transcript = transcript_list.find_transcript(['ur'])
                final_transcript = transcript.fetch()
                logger.info("Found Urdu transcript")
            except Exception as e:
                logger.debug(f"No Urdu transcript found: {e}")
            
            # Try Hindi transcript next
            if not final_transcript:
                try:
                    transcript = transcript_list.find_transcript(['hi'])
                    hindi_transcript = transcript.fetch()
                    # Convert Hindi transcript to Urdu script
                    final_transcript = [
                        {**segment, 'text': self.convert_devanagari_to_urdu(segment['text'])}
                        for segment in hindi_transcript
                    ]
                    logger.info("Found Hindi transcript and converted to Urdu")
                except Exception as e:
                    logger.debug(f"No Hindi transcript found or conversion failed: {e}")
            
            # Fall back to English if available
            if not final_transcript:
                try:
                    transcript = transcript_list.find_transcript(['en'])
                    final_transcript = transcript.fetch()
                    logger.info("Using English transcript as fallback")
                except Exception as e:
                    logger.debug(f"No English transcript found: {e}")
            
            # If no preferred language found, get the first available transcript
            if not final_transcript:
                try:
                    transcript = transcript_list.find_transcript(['ur', 'hi', 'en'])
                    final_transcript = transcript.fetch()
                    logger.info("Using first available transcript")
                except Exception as e:
                    logger.error(f"Could not find any transcript: {e}")
                    raise
            
            # Store in cache
            if final_transcript:
                cache_data = {
                    "video_id": video_id,
                    "transcript": final_transcript,
                    "timestamp": str(datetime.now())
                }
                self._write_cache(video_id, cache_data)
                logger.info(f"Cached transcript for video {video_id}")
                return final_transcript
            
            raise Exception("No transcript found in any supported language")
            
        except Exception as e:
            logger.error(f"Error getting transcript: {e}")
            raise

    def convert_devanagari_to_urdu(self, text: str) -> str:
        """Convert Hindi (Devanagari) text to Urdu script using AWS Translate with fallback to character mapping."""
        try:
            # First try AWS Translate
            try:
                response = self.translate_client.translate_text(
                    Text=text,
                    SourceLanguageCode='hi',
                    TargetLanguageCode='ur'
                )
                return response['TranslatedText']
            except Exception as e:
                logger.warning(f"AWS Translate failed, falling back to character mapping: {e}")
            
            # Basic Hindi to Urdu character mapping
            hindi_to_urdu = {
                'अ': 'ا',
                'आ': 'آ',
                'इ': 'ا',
                'ई': 'ای',
                'उ': 'ا',
                'ऊ': 'او',
                'ए': 'ے',
                'ऐ': 'ای',
                'ओ': 'او',
                'औ': 'او',
                'क': 'ک',
                'ख': 'کھ',
                'ग': 'گ',
                'घ': 'گھ',
                'ङ': 'نگ',
                'च': 'چ',
                'छ': 'چھ',
                'ज': 'ج',
                'झ': 'جھ',
                'ञ': 'نج',
                'ट': 'ٹ',
                'ठ': 'ٹھ',
                'ड': 'ڈ',
                'ढ': 'ڈھ',
                'ण': 'ن',
                'त': 'ت',
                'थ': 'تھ',
                'द': 'د',
                'ध': 'دھ',
                'न': 'ن',
                'प': 'پ',
                'फ': 'پھ',
                'ब': 'ب',
                'भ': 'بھ',
                'म': 'م',
                'य': 'ی',
                'र': 'ر',
                'ल': 'ل',
                'व': 'و',
                'श': 'ش',
                'ष': 'श',
                'स': 'س',
                'ह': 'ہ',
                'ा': 'ا',
                'ि': 'ِ',
                'ी': 'ی',
                'ु': 'ُ',
                'ू': 'و',
                'े': 'ے',
                'ै': 'ے',
                'ो': 'و',
                'ौ': 'و',
                'ं': 'ں',
                'ः': '',
                '़': '',
                '्': '',
                '।': '۔',
                '॥': '۔',
            }
            
            # Convert text character by character
            urdu_text = ''
            i = 0
            while i < len(text):
                # Handle special cases for combined characters
                if i + 1 < len(text) and text[i:i+2] in hindi_to_urdu:
                    urdu_text += hindi_to_urdu[text[i:i+2]]
                    i += 2
                elif text[i] in hindi_to_urdu:
                    urdu_text += hindi_to_urdu[text[i]]
                    i += 1
                else:
                    urdu_text += text[i]
                    i += 1
            
            # Post-processing fixes
            urdu_text = urdu_text.replace('  ', ' ')  # Remove double spaces
            urdu_text = urdu_text.strip()  # Remove leading/trailing spaces
            
            return urdu_text
            
        except Exception as e:
            logger.error(f"Error converting text to Urdu: {e}")
            return text  # Return original text if conversion fails

    def extract_urdu_segments(self, transcript: List[Dict]) -> List[Dict]:
        """Extract segments that contain Urdu text."""
        urdu_segments = []
        for segment in transcript:
            text = segment['text']
            # Basic check for Urdu/Arabic script (very simple heuristic)
            if any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text):
                urdu_segments.append(segment)
        return urdu_segments

    def generate_questions_with_bedrock(self, transcript: List[Dict], num_questions: int = 5) -> List[Dict]:
        """Generate questions using AWS Bedrock."""
        if not self._runtime:
            logger.warning("AWS Bedrock not available, falling back to basic questions")
            return self.generate_questions(transcript)
            
        try:
            # Combine relevant transcript segments
            urdu_segments = self.extract_urdu_segments(transcript)
            if not urdu_segments:
                logger.warning("No Urdu segments found in transcript")
                return self.generate_questions(transcript)  # Fall back to basic questions
                
            # Prepare context for the model
            context = "\n".join(f"Segment {i+1} (Time {segment['start']:.1f}s - {segment['start'] + segment['duration']:.1f}s):\n{segment['text']}" 
                              for i, segment in enumerate(urdu_segments))
            logger.info(f"Prepared context with {len(urdu_segments)} segments")
            
            # Prompt for Claude model
            prompt = f"""You are an expert in Urdu language teaching. I will provide you with transcript segments from an Urdu audio/video. Generate {num_questions} multiple-choice questions that test listening comprehension.

Important Rules:
1. Write ALL text (questions, options, everything) in Urdu script ONLY - no Roman Urdu or English
2. Questions should test understanding of specific details from the audio
3. Make questions progressively harder
4. Options should be plausible but clearly distinguishable
5. Include exact timestamps from the segments for audio reference
6. Each question must correspond to a specific segment and use its timestamps
7. CRITICAL: The correct_answer MUST EXACTLY match one of the options

Here is the transcript with timestamps:

{context}

Generate a JSON array of {num_questions} questions. Each question must have this exact format:
{{
  "id": (number),
  "question": "(question text in Urdu script)",
  "options": ["(option 1 in Urdu)", "(option 2 in Urdu)", "(option 3 in Urdu)", "(option 4 in Urdu)"],
  "correct_answer": "(correct option in Urdu - must match EXACTLY one of the options)",
  "audio_start": (start time in seconds, from the segment),
  "audio_end": (end time in seconds, start + duration)
}}

Return ONLY the JSON array, no other text. Ensure all text is in Urdu script and the correct_answer matches EXACTLY one of the options."""

            logger.info("Calling Bedrock with Claude model...")
            # Call Bedrock with Claude model
            body = json.dumps({
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant: Here are the questions in JSON format:",
                "max_tokens_to_sample": 2000,
                "temperature": 0.7,
                "top_k": 250,
                "top_p": 0.7,
                "stop_sequences": ["\n\nHuman:"]
            })
            
            response = self._runtime.invoke_model(
                modelId='anthropic.claude-v2',
                body=body.encode(),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            logger.info("Received response from Bedrock")
            
            # Extract the JSON part from the response
            response_text = response_body.get('completion', '')
            # Find the JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                try:
                    questions = json.loads(json_str)
                    logger.info(f"Successfully parsed {len(questions)} questions from response")
                    
                    # Validate question format and fix any issues
                    validated_questions = []
                    for i, q in enumerate(questions):
                        try:
                            # Validate required fields
                            if not all(k in q for k in ['id', 'question', 'options', 'correct_answer', 'audio_start', 'audio_end']):
                                logger.error(f"Question {i+1} missing required fields")
                                continue
                                
                            # Validate options
                            if not isinstance(q['options'], list) or len(q['options']) != 4:
                                logger.error(f"Question {i+1} has invalid options format")
                                continue
                                
                            # Validate correct answer
                            if q['correct_answer'] not in q['options']:
                                # Try to find the closest match
                                for opt in q['options']:
                                    if opt.strip() == q['correct_answer'].strip():
                                        q['correct_answer'] = opt
                                        break
                                if q['correct_answer'] not in q['options']:
                                    logger.error(f"Question {i+1} correct answer not in options")
                                    continue
                                    
                            # Add to validated questions
                            validated_questions.append(q)
                            logger.info(f"Question {i+1} format: {list(q.keys())}")
                            logger.info(f"Question {i+1} options count: {len(q['options'])}")
                            logger.info(f"Question {i+1} correct answer in options: {q['correct_answer'] in q['options']}")
                            
                        except Exception as e:
                            logger.error(f"Error validating question {i+1}: {e}")
                            continue
                    
                    if validated_questions:
                        logger.info(f"Generated {len(validated_questions)} questions")
                        return validated_questions
                    else:
                        logger.error("No valid questions after validation")
                        return self.generate_questions(transcript)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse questions JSON: {e}")
                    return self.generate_questions(transcript)
            else:
                logger.error("No JSON array found in response")
                return self.generate_questions(transcript)
                
        except Exception as e:
            logger.error(f"Error generating questions with Bedrock: {e}")
            return self.generate_questions(transcript)

    def generate_questions(self, transcript: List[Dict], num_questions: int = 5) -> List[Dict]:
        """Generate basic multiple-choice questions from transcript segments."""
        try:
            # Get Urdu segments
            urdu_segments = self.extract_urdu_segments(transcript)
            if not urdu_segments:
                logger.warning("No Urdu segments found for basic question generation")
                return []
                
            # Select segments for questions
            selected_segments = urdu_segments[:num_questions]
            questions = []
            
            for i, segment in enumerate(selected_segments):
                # Create a simple comprehension question
                question = {
                    "id": i + 1,
                    "question": f"اس حصے میں کیا کہا گیا ہے؟",  # "What was said in this segment?"
                    "options": [
                        segment['text'],  # Correct answer is the actual text
                        "یہ متن دستیاب نہیں ہے",  # "This text is not available"
                        "کچھ اور کہا گیا تھا",  # "Something else was said"
                        "مجھے سمجھ نہیں آیا"  # "I didn't understand"
                    ],
                    "correct_answer": segment['text'],
                    "audio_start": segment['start'],
                    "audio_end": segment['start'] + segment['duration']
                }
                questions.append(question)
                
            return questions
            
        except Exception as e:
            logger.error(f"Error generating basic questions: {e}")
            return []

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
                logger.info(f"Got transcript with {len(transcript)} segments")
            except Exception as e:
                logger.error(f"Error getting transcript: {e}")
                return {"error": str(e)}

            # Generate questions
            try:
                questions = self.generate_questions_with_bedrock(transcript)
                logger.info(f"Generated {len(questions)} questions")
                
                # Validate questions
                if not questions:
                    logger.error("No questions were generated")
                    return {"error": "Failed to generate questions"}
                    
                # Log question format for debugging
                for i, q in enumerate(questions):
                    logger.info(f"Question {i+1} format: {list(q.keys())}")
                    logger.info(f"Question {i+1} options count: {len(q.get('options', []))}")
                    if 'correct_answer' in q:
                        logger.info(f"Question {i+1} correct answer in options: {q['correct_answer'] in q.get('options', [])}")
                
                return {"questions": questions}
                
            except Exception as e:
                logger.error(f"Error generating questions: {e}")
                return {"error": f"Failed to generate questions: {str(e)}"}

        except Exception as e:
            logger.error(f"Error in get_questions_for_video: {e}")
            return {"error": str(e)}

    def get_transcript_with_stats(self, video_url: str) -> Dict:
        """Get transcript and generate statistics."""
        try:
            video_id = self.extract_video_id(video_url)
            transcript = self.get_transcript(video_id)
            
            if not transcript:
                return {
                    "transcript": [],
                    "statistics": {
                        "total_duration": 0,
                        "total_words": 0,
                        "avg_words_per_minute": 0,
                        "segments_count": 0,
                        "top_words": {}
                    }
                }
            
            # Calculate statistics
            total_duration = sum(segment['duration'] for segment in transcript)
            total_words = sum(len(segment['text'].split()) for segment in transcript)
            avg_words_per_minute = (total_words / total_duration) * 60 if total_duration > 0 else 0
            
            # Get word frequency using Counter
            words = [word.strip('.,!?()[]{}":;') for segment in transcript 
                    for word in segment['text'].split()]
            word_freq = Counter(word.lower() for word in words if word)
            
            # Get top 10 most frequent words
            top_words = dict(word_freq.most_common(10))
            
            stats = {
                "total_duration": round(total_duration, 2),
                "total_words": total_words,
                "avg_words_per_minute": round(avg_words_per_minute, 2),
                "segments_count": len(transcript),
                "top_words": top_words
            }
            
            return {
                "transcript": transcript,
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Error getting transcript with stats: {e}")
            return {
                "transcript": [],
                "statistics": {
                    "total_duration": 0,
                    "total_words": 0,
                    "avg_words_per_minute": 0,
                    "segments_count": 0,
                    "top_words": {}
                }
            }
