import boto3
import os
import logging
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict
import uuid
from datetime import datetime
from .script_converter import ScriptConverter
import re

logger = logging.getLogger(__name__)

class TextToSpeechService:
    def __init__(self):
        self.client = boto3.client('polly',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Initialize script converter
        self.converter = ScriptConverter()
        
        # Create audio cache directory if it doesn't exist
        self.cache_dir = "/app/audio_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Get API URL from environment - use internal Docker network URL
        self.api_url = os.getenv('API_URL', 'http://api:8002')
        
        logger.info("Text-to-Speech service initialized")
    
    def _create_ssml(self, text: str, lang: str = 'hi-IN') -> str:
        """Create SSML with prosody and break controls for more natural speech."""
        # For Hindi text, replace special markers with phoneme tags
        if lang == 'hi-IN':
            text = text.replace('__F__', '<phoneme alphabet="ipa" ph="f">फ</phoneme>')
            
        # Split text into sentences
        delimiter = '।' if lang == 'hi-IN' else '.'
        sentences = text.split(delimiter)
        
        # Build SSML with prosody controls
        ssml_parts = ['<speak>']
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # Add prosody controls for more natural rhythm
            # Slightly different settings for English vs Hindi
            rate = "85%" if lang == 'hi-IN' else "95%"
            ssml_parts.append(
                f'<prosody rate="{rate}" pitch="+0%">{sentence.strip()}</prosody>'
                '<break strength="strong"/>'
            )
        
        ssml_parts.append('</speak>')
        return ''.join(ssml_parts)
    
    async def generate_audio(self, text: str, lang: str = 'hi-IN') -> Optional[str]:
        """Generate audio using Amazon Polly.
        For Hindi text, converts from Urdu script to Devanagari while preserving pronunciation.
        For English text, uses native English voice."""
        try:
            # Process text based on language
            if lang == 'hi-IN':
                # Convert Urdu script to Devanagari
                processed_text = self.converter.convert_to_devanagari(text)
                voice_id = 'Aditi'
                logger.info("Converted text to Devanagari script")
            else:
                # Use English text as is
                processed_text = text
                voice_id = 'Joanna'  # Female US English voice
                logger.info("Using English text directly")
            
            # Create SSML with prosody controls
            ssml_text = self._create_ssml(processed_text, lang)
            logger.info("Created SSML with prosody controls")
            
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.mp3"
            filepath = os.path.join(self.cache_dir, filename)
            
            # Request speech synthesis
            response = self.client.synthesize_speech(
                Text=ssml_text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode=lang,
                Engine='standard',
                TextType='ssml'
            )
            
            # Save the audio stream to a file
            if "AudioStream" in response:
                with open(filepath, 'wb') as file:
                    file.write(response['AudioStream'].read())
                
                logger.info(f"Generated audio file: {filename}")
                # Return just the filename instead of full URL
                return filename
            
            return None
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Polly error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Audio generation error: {str(e)}")
            raise
    
    async def generate_all_audio(self, text_dict: Dict[str, str]) -> Dict[str, str]:
        """Generate audio for all provided text versions."""
        result = {}
        for lang, text in text_dict.items():
            if text:
                audio_filename = await self.generate_audio(
                    text,
                    'hi-IN' if lang == 'ur' else 'en-US'
                )
                if audio_filename:
                    result[f"{lang}_audio"] = f"/audio/{audio_filename}"
        return result
    
    async def cleanup_old_audio(self, max_age_hours: int = 24) -> None:
        """Clean up audio files older than specified hours."""
        try:
            current_time = datetime.now()
            
            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                file_age = current_time - datetime.fromtimestamp(os.path.getctime(filepath))
                
                if file_age.total_seconds() > (max_age_hours * 3600):
                    os.remove(filepath)
                    logger.info(f"Removed old audio file: {filename}")
                    
        except Exception as e:
            logger.error(f"Error during audio cleanup: {str(e)}")
            raise
