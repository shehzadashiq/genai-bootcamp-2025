"""
AWS Configuration for Language Portal Backend.
Includes settings for Bedrock, Translate, and Polly services.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Credentials
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Bedrock Configuration
BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'amazon.titan-embed-text-v1')
BEDROCK_MAX_TOKENS = int(os.getenv('BEDROCK_MAX_TOKENS', '1024'))
BEDROCK_TEMPERATURE = float(os.getenv('BEDROCK_TEMPERATURE', '0.7'))

# Translate Configuration
TRANSLATE_SOURCE_LANG = 'hi'  # Hindi
TRANSLATE_TARGET_LANG = 'ur'  # Urdu

# Polly Configuration
POLLY_VOICE_ID = os.getenv('POLLY_VOICE_ID', 'Aditi')  # Default to Aditi for Hindi/Urdu
POLLY_OUTPUT_FORMAT = 'mp3'

# Error Messages
AWS_ERROR_MESSAGES = {
    'bedrock': 'Error accessing AWS Bedrock service. Please check your credentials and permissions.',
    'translate': 'Error accessing AWS Translate service. Please check your credentials and permissions.',
    'polly': 'Error accessing AWS Polly service. Please check your credentials and permissions.',
    'credentials': 'AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.',
}

def validate_aws_config():
    """Validate AWS configuration and required permissions."""
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
        raise ValueError(AWS_ERROR_MESSAGES['credentials'])
    
    required_permissions = [
        'bedrock:ListFoundationModels',
        'bedrock:InvokeModel',
        'bedrock-runtime:InvokeModel',
        'translate:TranslateText',
        'translate:ListLanguages',
        'polly:DescribeVoices',
        'polly:SynthesizeSpeech',
    ]
    
    return {
        'credentials': {
            'aws_access_key_id': AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': AWS_SECRET_ACCESS_KEY,
            'region_name': AWS_REGION,
        },
        'required_permissions': required_permissions,
        'services': {
            'bedrock': {
                'model_id': BEDROCK_MODEL_ID,
                'max_tokens': BEDROCK_MAX_TOKENS,
                'temperature': BEDROCK_TEMPERATURE,
            },
            'translate': {
                'source_lang': TRANSLATE_SOURCE_LANG,
                'target_lang': TRANSLATE_TARGET_LANG,
            },
            'polly': {
                'voice_id': POLLY_VOICE_ID,
                'output_format': POLLY_OUTPUT_FORMAT,
            },
        },
    }
