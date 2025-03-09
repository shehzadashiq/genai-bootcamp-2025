"""
Validation module for Hindi-Urdu translation functionality.
Ensures proper configuration and operation of translation services.
"""
import boto3
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Tuple
from config import aws_config
from hindi_urdu_converter import HindiUrduConverter

class TranslationValidationError(Exception):
    """Custom exception for translation validation errors."""
    pass

def validate_aws_translate_access() -> Tuple[bool, str]:
    """
    Validate AWS Translate access and Hindi-Urdu language pair support.
    """
    try:
        translate = boto3.client(
            'translate',
            region_name=aws_config.AWS_REGION
        )
        
        # Test basic translation access
        test_text = "नमस्ते"  # Hello in Hindi
        response = translate.translate_text(
            Text=test_text,
            SourceLanguageCode='hi',
            TargetLanguageCode='ur'
        )
        
        if not response['TranslatedText']:
            return False, "AWS Translate returned empty translation"
            
        return True, "AWS Translate Hindi-Urdu translation validated"
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnsupportedLanguagePairException':
            return False, "Hindi-Urdu translation pair not supported"
        elif error_code == 'UnauthorizedException':
            return False, "Missing translate:TranslateText permission"
        else:
            return False, f"AWS Translate validation failed: {str(e)}"

def validate_character_mapping_fallback() -> Tuple[bool, str]:
    """
    Validate the character mapping fallback system.
    Tests a comprehensive set of Hindi characters and combinations.
    """
    converter = HindiUrduConverter()
    
    # Test cases for Hindi to Urdu conversion
    test_cases = [
        ("क", "ک"),      # Basic consonant
        ("ख", "کھ"),     # Aspirated consonant
        ("आ", "آ"),      # Long vowel
        ("ि", "ِ"),      # Short vowel
        ("क्ष", "کش"),    # Conjunct consonant
        ("१२३", "١٢٣"),  # Numerals
        ("।", "۔"),      # Punctuation
        ("नमस्ते दुनिया", "نمستے دنیا"),  # Full phrase
        ("हिंदी उर्दू", "ہندی اردو"),      # Language names
        ("क्या हाल है?", "کیا حال ہے؟")    # Question with punctuation
    ]
    
    failures = []
    for hindi, expected_urdu in test_cases:
        result = converter.convert(hindi)
        if result != expected_urdu:
            failures.append(f"{hindi} -> {result} (expected {expected_urdu})")
            
    if failures:
        return False, f"Character mapping failures: {', '.join(failures)}"
        
    return True, "Character mapping fallback system validated"

def validate_translation_config() -> Tuple[bool, str]:
    """
    Validate the complete translation configuration including AWS Translate
    and fallback system.
    """
    # First check AWS Translate
    aws_success, aws_message = validate_aws_translate_access()
    
    # If AWS Translate fails and fallback is enabled, check fallback system
    if not aws_success and aws_config.TRANSLATION_FALLBACK:
        fallback_success, fallback_message = validate_character_mapping_fallback()
        
        if fallback_success:
            return True, "Fallback translation system validated (AWS Translate unavailable)"
        else:
            return False, f"Both AWS Translate and fallback system failed:\n" \
                         f"AWS: {aws_message}\n" \
                         f"Fallback: {fallback_message}"
    
    # If AWS Translate succeeds, we're good (even if fallback fails)
    elif aws_success:
        return True, "AWS Translate validated successfully"
    
    # If AWS Translate fails and fallback is disabled, that's an error
    else:
        return False, f"AWS Translate failed and fallback is disabled: {aws_message}"

def test_translation_pipeline(text: str = "नमस्ते दुनिया") -> Dict:
    """
    Test the complete translation pipeline with a sample text.
    Returns detailed results of each step.
    """
    results = {
        'input_text': text,
        'aws_translate': {'success': False, 'output': None, 'error': None},
        'fallback': {'success': False, 'output': None, 'error': None},
        'final_output': None
    }
    
    try:
        # Try AWS Translate first
        translate = boto3.client(
            'translate',
            region_name=aws_config.AWS_REGION
        )
        
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode='hi',
            TargetLanguageCode='ur'
        )
        
        results['aws_translate'] = {
            'success': True,
            'output': response['TranslatedText'],
            'error': None
        }
        results['final_output'] = response['TranslatedText']
        
    except Exception as e:
        results['aws_translate']['error'] = str(e)
        
        # Try fallback if enabled
        if aws_config.TRANSLATION_FALLBACK:
            try:
                converter = HindiUrduConverter()
                fallback_output = converter.convert(text)
                
                results['fallback'] = {
                    'success': True,
                    'output': fallback_output,
                    'error': None
                }
                results['final_output'] = fallback_output
                
            except Exception as fallback_e:
                results['fallback']['error'] = str(fallback_e)
    
    return results

if __name__ == '__main__':
    # Run translation validation
    print("\nTranslation System Validation")
    print("============================")
    
    success, message = validate_translation_config()
    print(f"\nStatus: {'✓' if success else '✗'}")
    print(f"Message: {message}")
    
    # Test translation pipeline with various inputs
    test_inputs = [
        "नमस्ते दुनिया",  # Hello World
        "क्या हाल है?",   # How are you?
        "हिंदी और उर्दू", # Hindi and Urdu
        "१२३४५",         # Numbers
        "वाक्य में विराम चिह्न।"  # Sentence with punctuation
    ]
    
    print("\nTranslation Pipeline Tests")
    print("=========================")
    
    for test_text in test_inputs:
        print(f"\nTest Input: {test_text}")
        results = test_translation_pipeline(test_text)
        
        print("\nAWS Translate:")
        print(f"Success: {'✓' if results['aws_translate']['success'] else '✗'}")
        if results['aws_translate']['output']:
            print(f"Output: {results['aws_translate']['output']}")
        if results['aws_translate']['error']:
            print(f"Error: {results['aws_translate']['error']}")
            
        if aws_config.TRANSLATION_FALLBACK:
            print("\nFallback System:")
            print(f"Success: {'✓' if results['fallback']['success'] else '✗'}")
            if results['fallback']['output']:
                print(f"Output: {results['fallback']['output']}")
            if results['fallback']['error']:
                print(f"Error: {results['fallback']['error']}")
        
        print(f"\nFinal Output: {results['final_output']}")
