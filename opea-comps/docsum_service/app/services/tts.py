import boto3
import os
import logging
from botocore.exceptions import ClientError, BotoCoreError
from typing import Optional, Dict
import uuid
from datetime import datetime
from google.cloud import texttospeech
import re

logger = logging.getLogger(__name__)

class TextToSpeechService:
    def __init__(self):
        # Initialize AWS Polly client
        self.polly_client = boto3.client('polly',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Initialize Google Cloud Text-to-Speech client if credentials are available
        self.google_client = None
        try:
            self.google_client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud Text-to-Speech client initialized successfully")
        except Exception as e:
            logger.warning(f"Google Cloud Text-to-Speech client initialization failed: {str(e)}")
            logger.warning("Will use AWS Polly for all languages including Urdu")
        
        # Create audio cache directory if it doesn't exist
        self.cache_dir = "/app/audio_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Get API URL from environment - use internal Docker network URL
        self.api_url = os.getenv('API_URL', 'http://api:8002')
        
        logger.info("Text-to-Speech service initialized")
    
    def _create_ssml(self, text: str, lang: str = 'hi-IN') -> str:
        """Create SSML with prosody and break controls for more natural speech."""
        # Split text into sentences
        delimiter = '।' if lang in ['hi-IN', 'ur-PK'] else '.'
        sentences = text.split(delimiter)
        
        # Build SSML with prosody controls
        ssml_parts = ['<speak>']
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            # Add prosody controls for more natural rhythm
            rate = "85%" if lang in ['hi-IN', 'ur-PK'] else "95%"
            ssml_parts.append(
                f'<prosody rate="{rate}" pitch="+0%">{sentence.strip()}</prosody>'
                '<break strength="strong"/>'
            )
        
        ssml_parts.append('</speak>')
        return ''.join(ssml_parts)
    
    async def generate_audio(self, text: str, lang: str = 'hi-IN') -> Optional[str]:
        """Generate audio using either Google Cloud TTS (for Urdu) or Amazon Polly (for other languages)."""
        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.mp3"
            filepath = os.path.join(self.cache_dir, filename)
            logger.info(f"Will save audio to: {filepath}")

            if self.google_client and lang == 'ur-PK':
                # Use Google Cloud Text-to-Speech for Urdu
                try:
                    synthesis_input = texttospeech.SynthesisInput(text=text)
                    
                    # Build the voice request
                    voice = texttospeech.VoiceSelectionParams(
                        language_code='ur-PK',  # Urdu (Pakistan)
                        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                    )
                    
                    # Select the type of audio file
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3,
                        speaking_rate=0.85  # Slightly slower for better clarity
                    )
                    
                    # Perform the text-to-speech request
                    response = self.google_client.synthesize_speech(
                        input=synthesis_input,
                        voice=voice,
                        audio_config=audio_config
                    )
                    
                    # Save the audio stream to a file
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'wb') as file:
                        file.write(response.audio_content)
                    
                    logger.info("Generated Urdu audio using Google Cloud TTS")
                    
                except Exception as e:
                    logger.warning(f"Google TTS failed for Urdu, falling back to AWS Polly: {str(e)}")
                    # Fall back to AWS Polly for Urdu
                    voice_id = 'Aditi'  # Use Hindi voice as fallback for Urdu
                    ssml_text = self._create_ssml(text, 'hi-IN')
                    
                    # Request speech synthesis from Polly
                    response = self.polly_client.synthesize_speech(
                        Text=ssml_text,
                        OutputFormat='mp3',
                        VoiceId=voice_id,
                        LanguageCode='hi-IN',
                        Engine='standard',
                        TextType='ssml'
                    )
                    
                    # Save the audio stream to a file
                    if "AudioStream" in response:
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        with open(filepath, 'wb') as file:
                            file.write(response['AudioStream'].read())
                        logger.info("Generated Urdu audio using AWS Polly with Hindi voice as fallback")
            else:
                # Use Amazon Polly for other languages
                voice_id = 'Joanna' if lang == 'en-US' else 'Aditi'  # Aditi for Hindi
                ssml_text = self._create_ssml(text, lang)
                
                # Request speech synthesis from Polly
                response = self.polly_client.synthesize_speech(
                    Text=ssml_text,
                    OutputFormat='mp3',
                    VoiceId=voice_id,
                    LanguageCode=lang,
                    Engine='standard',
                    TextType='ssml'
                )
                
                # Save the audio stream to a file
                if "AudioStream" in response:
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, 'wb') as file:
                        file.write(response['AudioStream'].read())
                    logger.info(f"Generated audio using Amazon Polly for language {lang}")
            
            # Return just the filename
            return filename
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Polly error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Audio generation error: {str(e)}")
            return None

    async def generate_all_audio(self, content: Dict[str, str]) -> Dict[str, str]:
        """Generate audio for all available text content."""
        result = {}
        for lang, text in content.items():
            if text:
                audio_filename = await self.generate_audio(
                    text,
                    'ur-PK' if lang == 'ur' else 'en-US' if lang == 'en' else 'hi-IN'
                )
                if audio_filename:
                    result[f"{lang}_audio"] = f"/audio/{audio_filename}"
        return result

    async def cleanup_old_audio(self, max_age_hours: int = 24):
        """Clean up audio files older than specified hours."""
        try:
            current_time = datetime.now()
            for filename in os.listdir(self.cache_dir):
                filepath = os.path.join(self.cache_dir, filename)
                if os.path.isfile(filepath):
                    file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    age_hours = (current_time - file_time).total_seconds() / 3600
                    if age_hours > max_age_hours:
                        os.remove(filepath)
                        logger.info(f"Removed old audio file: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning up audio files: {str(e)}")
