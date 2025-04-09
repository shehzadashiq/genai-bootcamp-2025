import os
import logging
from typing import Optional
import uuid
from google.cloud import texttospeech
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

class TextToSpeechService:
    def __init__(self):
        # Get credentials file path - using absolute path from project root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        credentials_path = os.path.join(base_dir, 'credentials', 'google_credentials.json')
        
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Google credentials file not found at {credentials_path}")
        
        # Initialize Google Cloud Text-to-Speech client with credentials
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        self.google_client = texttospeech.TextToSpeechClient(credentials=credentials)
        
        # Create audio cache directory if it doesn't exist
        self.cache_dir = os.path.join(base_dir, "audio_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"Text-to-Speech service initialized with credentials from {credentials_path}")
    
    def generate_audio(self, text: str) -> Optional[str]:
        """Generate audio using Google Cloud TTS for Urdu."""
        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.mp3"
            filepath = os.path.join(self.cache_dir, filename)
            logger.info(f"Will save audio to: {filepath}")

            # Use Google Cloud Text-to-Speech for Urdu
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
            
            # Return just the filename
            return filename
            
        except Exception as e:
            logger.error(f"Audio generation error: {str(e)}")
            return None
