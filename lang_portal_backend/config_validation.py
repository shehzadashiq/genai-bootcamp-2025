"""
Configuration validation for the Language Listening Application.
Ensures all settings are valid and compatible.
"""
from typing import Dict, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import json
from config import (
    guardrails_config,
    aws_config,
    vector_store_config,
    app_config
)
from translation_validation import (
    validate_translation_config,
    test_translation_pipeline,
    TranslationValidationError
)

class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass

def validate_aws_credentials() -> Tuple[bool, str]:
    """Validate AWS credentials and permissions."""
    try:
        # Check AWS credentials
        sts = boto3.client(
            'sts',
            aws_access_key_id=aws_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=aws_config.AWS_SECRET_ACCESS_KEY,
            region_name=aws_config.AWS_REGION
        )
        sts.get_caller_identity()
        
        # Test Bedrock access
        bedrock = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        bedrock.list_foundation_models()
        
        # Test Polly access
        polly = boto3.client(
            'polly',
            region_name=aws_config.AWS_REGION
        )
        polly.describe_voices()
        
        # Test Translate access
        translate = boto3.client(
            'translate',
            region_name=aws_config.AWS_REGION
        )
        translate.list_languages()
        
        return True, "AWS credentials and permissions validated"
    except ClientError as e:
        return False, f"AWS validation failed: {str(e)}"

def validate_bedrock_models() -> Tuple[bool, str]:
    """Validate Bedrock model configurations."""
    try:
        bedrock = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        
        # Check if models exist
        models = bedrock.list_foundation_models()
        available_models = [m['modelId'] for m in models['models']]
        
        if aws_config.BEDROCK_MODEL_ID not in available_models:
            return False, f"Bedrock model {aws_config.BEDROCK_MODEL_ID} not available"
            
        if aws_config.BEDROCK_EMBEDDING_MODEL not in available_models:
            return False, f"Bedrock embedding model {aws_config.BEDROCK_EMBEDDING_MODEL} not available"
            
        return True, "Bedrock models validated"
    except ClientError as e:
        return False, f"Bedrock validation failed: {str(e)}"

def validate_polly_voice() -> Tuple[bool, str]:
    """Validate Polly voice configuration."""
    try:
        polly = boto3.client(
            'polly',
            region_name=aws_config.AWS_REGION
        )
        
        # Check if voice exists and supports Urdu
        voices = polly.describe_voices(LanguageCode='ur-PK')
        available_voices = [v['Id'] for v in voices['Voices']]
        
        if aws_config.POLLY_VOICE_ID not in available_voices:
            return False, f"Polly voice {aws_config.POLLY_VOICE_ID} not available for Urdu"
            
        return True, "Polly voice validated"
    except ClientError as e:
        return False, f"Polly validation failed: {str(e)}"

def validate_translation_setup() -> Tuple[bool, str]:
    """
    Validate translation setup including AWS Translate and fallback system.
    """
    try:
        # Run translation validation
        success, message = validate_translation_config()
        if not success:
            return False, message
            
        # Test translation pipeline with sample text
        results = test_translation_pipeline()
        if not results['final_output']:
            return False, "Translation pipeline test failed to produce output"
            
        return True, "Translation setup validated successfully"
    except Exception as e:
        return False, f"Translation setup validation failed: {str(e)}"

def validate_guardrails_config() -> Tuple[bool, str]:
    """Validate guardrails configuration."""
    try:
        # Validate rate limiting
        if guardrails_config.RATE_LIMIT_REQUESTS <= 0:
            return False, "Rate limit requests must be positive"
        if guardrails_config.RATE_LIMIT_WINDOW <= 0:
            return False, "Rate limit window must be positive"
            
        # Validate thresholds
        if not 0 <= guardrails_config.TOXIC_CONTENT_THRESHOLD <= 1:
            return False, "Toxic content threshold must be between 0 and 1"
        if not 0 <= guardrails_config.LANGUAGE_CONFIDENCE_THRESHOLD <= 1:
            return False, "Language confidence threshold must be between 0 and 1"
            
        # Validate audio duration limits
        if guardrails_config.MIN_AUDIO_DURATION <= 0:
            return False, "Minimum audio duration must be positive"
        if guardrails_config.MAX_AUDIO_DURATION <= guardrails_config.MIN_AUDIO_DURATION:
            return False, "Maximum audio duration must be greater than minimum"
            
        return True, "Guardrails configuration validated"
    except Exception as e:
        return False, f"Guardrails validation failed: {str(e)}"

def validate_vector_store_config() -> Tuple[bool, str]:
    """Validate vector store configuration."""
    try:
        # Validate similarity metric
        valid_metrics = ['cosine', 'euclidean', 'dot_product']
        if vector_store_config.SIMILARITY_METRIC not in valid_metrics:
            return False, f"Invalid similarity metric. Must be one of: {valid_metrics}"
            
        # Validate embedding dimension
        if vector_store_config.EMBEDDING_DIMENSION <= 0:
            return False, "Embedding dimension must be positive"
            
        # Validate search settings
        if vector_store_config.DEFAULT_SEARCH_LIMIT <= 0:
            return False, "Default search limit must be positive"
        if not 0 <= vector_store_config.SIMILARITY_THRESHOLD <= 1:
            return False, "Similarity threshold must be between 0 and 1"
            
        return True, "Vector store configuration validated"
    except Exception as e:
        return False, f"Vector store validation failed: {str(e)}"

def validate_app_config() -> Tuple[bool, str]:
    """Validate application configuration."""
    try:
        # Validate exercise generation settings
        if app_config.QUESTIONS_PER_EXERCISE <= 0:
            return False, "Questions per exercise must be positive"
        if app_config.OPTIONS_PER_QUESTION < 2:
            return False, "Options per question must be at least 2"
            
        # Validate transcript length
        if app_config.MAX_TRANSCRIPT_LENGTH <= 0:
            return False, "Maximum transcript length must be positive"
            
        return True, "Application configuration validated"
    except Exception as e:
        return False, f"Application validation failed: {str(e)}"

def validate_all_configs() -> List[Dict[str, str]]:
    """
    Validate all configurations and return list of validation results.
    Each result contains 'component', 'status', and 'message'.
    """
    validations = [
        ('AWS Credentials', validate_aws_credentials),
        ('Bedrock Models', validate_bedrock_models),
        ('Polly Voice', validate_polly_voice),
        ('Translation Setup', validate_translation_setup),
        ('Guardrails', validate_guardrails_config),
        ('Vector Store', validate_vector_store_config),
        ('Application', validate_app_config)
    ]
    
    results = []
    for component, validator in validations:
        success, message = validator()
        results.append({
            'component': component,
            'status': 'valid' if success else 'invalid',
            'message': message
        })
    
    return results

if __name__ == '__main__':
    # Run all validations and print results
    results = validate_all_configs()
    print("\nConfiguration Validation Results:")
    print("=================================")
    for result in results:
        status_color = '\033[92m' if result['status'] == 'valid' else '\033[91m'
        print(f"\n{result['component']}:")
        print(f"Status: {status_color}{result['status']}\033[0m")
        print(f"Message: {result['message']}")
