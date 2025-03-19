import boto3
import os
import logging
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional
import uuid
from datetime import datetime
from .script_converter import ScriptConverter

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
        self.cache_dir = "audio_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info("Text-to-Speech service initialized")
    
    async def generate_audio(self, text: str) -> Optional[str]:
        """Generate audio from Urdu text using Amazon Polly.
        Converts Urdu script to Devanagari while preserving pronunciation,
        then uses Hindi voice for better quality speech."""
        try:
            # Convert Urdu script to Devanagari
            devanagari_text = self.converter.convert_to_devanagari(text)
            logger.info("Converted text to Devanagari script")
            
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.mp3"
            filepath = os.path.join(self.cache_dir, filename)
            
            # Request speech synthesis
            response = self.client.synthesize_speech(
                Text=devanagari_text,
                OutputFormat='mp3',
                VoiceId='Aditi',  # Hindi female voice
                LanguageCode='hi-IN',  # Hindi
                Engine='standard'
            )
            
            # Save the audio stream to a file
            if "AudioStream" in response:
                with open(filepath, 'wb') as file:
                    file.write(response['AudioStream'].read())
                
                logger.info(f"Generated audio file: {filename}")
                return filepath
            
            return None
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Polly error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Audio generation error: {str(e)}")
            raise
    
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
