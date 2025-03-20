import boto3
import logging
from botocore.exceptions import ClientError, BotoCoreError
import os
from typing import Optional

logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.client = boto3.client('translate',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        logger.info("Translation service initialized")
    
    async def translate_to_urdu(self, text: str) -> str:
        """Translate text to Urdu using Amazon Translate."""
        try:
            response = self.client.translate_text(
                Text=text,
                SourceLanguageCode='en',
                TargetLanguageCode='ur'
            )
            
            translated_text = response['TranslatedText']
            logger.info("Successfully translated text to Urdu")
            return translated_text
            
        except (ClientError, BotoCoreError) as e:
            logger.error(f"AWS Translation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            raise
    
    async def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of the input text."""
        try:
            response = self.client.detect_dominant_language(
                Text=text
            )
            
            if response['Languages']:
                return response['Languages'][0]['LanguageCode']
            
            return None
            
        except Exception as e:
            logger.error(f"Language detection error: {str(e)}")
            return None
