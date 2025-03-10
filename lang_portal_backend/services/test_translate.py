"""
Test AWS Translate functionality for English to Urdu translation.
"""
import os
import boto3
import botocore.config
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_translate():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize AWS Translate client
        config = botocore.config.Config(
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            retries={'max_attempts': 3},
            connect_timeout=5,
            read_timeout=10
        )
        
        translate = boto3.client(
            'translate',
            config=config,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        
        # Test text
        test_text = "Never gonna give you up, never gonna let you down"
        
        # Try translation
        response = translate.translate_text(
            Text=test_text,
            SourceLanguageCode='en',
            TargetLanguageCode='ur'
        )
        
        logger.info("Translation test results:")
        logger.info(f"Original text: {test_text}")
        logger.info(f"Translated text: {response['TranslatedText']}")
        logger.info(f"Source language code: {response['SourceLanguageCode']}")
        logger.info(f"Target language code: {response['TargetLanguageCode']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Translation test failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_translate()
    if success:
        logger.info("✓ Translation test completed successfully")
    else:
        logger.error("✗ Translation test failed")
