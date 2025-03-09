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
    """
    Validate AWS credentials and permissions.
    Tests access to required services: Bedrock and Translate.
    Polly is optional.
    """
    try:
        # Initialize service clients
        bedrock = boto3.client(
            'bedrock',  # Use base bedrock client for model listing
            region_name=aws_config.AWS_REGION
        )
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        translate = boto3.client(
            'translate',
            region_name=aws_config.AWS_REGION
        )
        
        # Test Bedrock access (required)
        bedrock.list_foundation_models()
        
        # Test Translate access (required)
        translate.list_languages()
        
        return True, "AWS credentials validated successfully"
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        return False, f"AWS validation failed: {error_code} - {error_msg}"

def validate_bedrock_models() -> Tuple[bool, str]:
    """Validate Bedrock model configurations."""
    try:
        # Initialize Bedrock client
        bedrock = boto3.client(
            'bedrock',  # Use base bedrock client for model listing
            region_name=aws_config.AWS_REGION
        )
        
        # List available models
        response = bedrock.list_foundation_models()
        
        # Extract model IDs from response
        available_models = [
            m['modelId'] for m in response.get('modelSummaries', [])
        ]
        
        # Check if configured models are available
        if aws_config.BEDROCK_MODEL_ID not in available_models:
            return False, f"Configured Bedrock model {aws_config.BEDROCK_MODEL_ID} not found in available models"
            
        if aws_config.BEDROCK_EMBEDDING_MODEL not in available_models:
            return False, f"Configured embedding model {aws_config.BEDROCK_EMBEDDING_MODEL} not found in available models"
            
        return True, "Bedrock models validated successfully"
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        return False, f"Bedrock model validation failed: {error_code} - {error_msg}"

def validate_polly_voice() -> Tuple[bool, str]:
    """
    Validate Polly voice configuration.
    This is optional - if Polly is not available, we'll use alternative TTS.
    """
    try:
        polly = boto3.client(
            'polly',
            region_name=aws_config.AWS_REGION
        )
        voices = polly.describe_voices()
        
        voice_ids = [v['Id'] for v in voices['Voices']]
        if aws_config.POLLY_VOICE_ID not in voice_ids:
            return False, f"Configured voice {aws_config.POLLY_VOICE_ID} not found"
            
        return True, "Polly voice validated successfully"
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException':
            print("Warning: Polly access not available. Will use alternative TTS.")
            return True, "Polly not available, using alternative TTS"
        return False, f"Polly validation failed: {e.response['Error']['Message']}"

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

def validate_all_configs() -> Dict[str, Tuple[bool, str]]:
    """
    Validate all configurations.
    Returns a dictionary of validation results.
    """
    validators = {
        'aws_credentials': validate_aws_credentials,
        'bedrock_models': validate_bedrock_models,
        'polly_voice': validate_polly_voice,
        'translation': validate_translation_setup,
        'guardrails': validate_guardrails_config,
        'vector_store': validate_vector_store_config,
        'app_config': validate_app_config
    }
    
    results = {}
    for name, validator in validators.items():
        try:
            success, message = validator()
            results[name] = (success, message)
            
            # Stop on critical failures (except Polly)
            if not success and name != 'polly_voice':
                break
                
        except Exception as e:
            results[name] = (False, str(e))
            if name != 'polly_voice':
                break
    
    return results

if __name__ == '__main__':
    # Run all validations and print results
    results = validate_all_configs()
    print("\nConfiguration Validation Results:")
    print("=================================")
    for name, (success, message) in results.items():
        status_color = '\033[92m' if success else '\033[91m'
        print(f"\n{name.capitalize().replace('_', ' ')}:")
        print(f"Status: {status_color}{('Valid' if success else 'Invalid')}\033[0m")
        print(f"Message: {message}")
