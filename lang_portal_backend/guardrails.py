"""
Guardrails implementation for the Language Listening Application.
Implements content safety, language validation, and rate limiting.
"""
import boto3
import time
from typing import Dict, List, Optional, Tuple
from functools import wraps
from config import guardrails_config, aws_config

class LanguageGuardrails:
    def __init__(self):
        self.translate_client = boto3.client(
            'translate',
            region_name=aws_config.AWS_REGION
        )
        self.comprehend_client = boto3.client(
            'comprehend',
            region_name=aws_config.AWS_REGION
        )
        self._rate_limit_store = {}
        
        # Load configurations
        self.SUPPORTED_LANGS = guardrails_config.SUPPORTED_LANGUAGES
        self.RATE_LIMIT = {
            'requests_per_minute': guardrails_config.RATE_LIMIT_REQUESTS,
            'window_size': guardrails_config.RATE_LIMIT_WINDOW
        }
        self.TOXIC_THRESHOLD = guardrails_config.TOXIC_CONTENT_THRESHOLD
        self.LANG_CONFIDENCE = guardrails_config.LANGUAGE_CONFIDENCE_THRESHOLD
        self.TRANSLATION_FALLBACK = aws_config.TRANSLATION_FALLBACK

    def validate_language(self, text: str, expected_lang: str) -> Tuple[bool, str]:
        """
        Validate if the text is in the expected language using Amazon Comprehend.
        """
        if expected_lang not in self.SUPPORTED_LANGS:
            return False, f"Language {expected_lang} is not supported"
            
        try:
            response = self.comprehend_client.detect_dominant_language(Text=text)
            detected_lang = response['Languages'][0]
            
            if detected_lang['LanguageCode'] != expected_lang:
                return False, f"Expected {expected_lang}, but detected {detected_lang['LanguageCode']}"
            
            if detected_lang['Score'] < self.LANG_CONFIDENCE:
                return False, f"Language confidence too low: {detected_lang['Score']:.2f}"
                
            return True, "Language validation passed"
            
        except Exception as e:
            return False, f"Language validation failed: {str(e)}"

    def check_content_safety(self, text: str) -> Tuple[bool, str]:
        """
        Check content for inappropriate material using Amazon Comprehend.
        """
        try:
            # First translate to English if not already in English
            if not self.is_english(text):
                response = self.translate_client.translate_text(
                    Text=text,
                    SourceLanguageCode='auto',
                    TargetLanguageCode='en'
                )
                text = response['TranslatedText']
            
            # Check for toxic content
            response = self.comprehend_client.detect_toxic_content(
                TextSegments=[{'Text': text}],
                LanguageCode='en'
            )
            
            # Analyze results
            for result in response['ResultList']:
                if any(label['Score'] > self.TOXIC_THRESHOLD for label in result['Labels']):
                    return False, "Content contains inappropriate material"
                    
            return True, "Content safety check passed"
            
        except Exception as e:
            return False, f"Content safety check failed: {str(e)}"

    def is_english(self, text: str) -> bool:
        """Helper method to detect if text is in English."""
        try:
            response = self.comprehend_client.detect_dominant_language(Text=text)
            return response['Languages'][0]['LanguageCode'] == 'en'
        except:
            return False

    def validate_audio_length(self, duration_seconds: float) -> Tuple[bool, str]:
        """
        Validate audio length is within acceptable bounds.
        """
        if duration_seconds < guardrails_config.MIN_AUDIO_DURATION:
            return False, f"Audio too short (minimum {guardrails_config.MIN_AUDIO_DURATION} seconds)"
        if duration_seconds > guardrails_config.MAX_AUDIO_DURATION:
            return False, f"Audio too long (maximum {guardrails_config.MAX_AUDIO_DURATION} seconds)"
        return True, "Audio length validation passed"

    def rate_limit(self, user_id: str) -> Tuple[bool, str]:
        """
        Implement rate limiting per user.
        """
        current_time = time.time()
        user_requests = self._rate_limit_store.get(user_id, [])
        
        # Remove old requests outside the window
        user_requests = [t for t in user_requests 
                        if current_time - t < self.RATE_LIMIT['window_size']]
        
        if len(user_requests) >= self.RATE_LIMIT['requests_per_minute']:
            return False, "Rate limit exceeded"
            
        user_requests.append(current_time)
        self._rate_limit_store[user_id] = user_requests
        return True, "Rate limit check passed"

def with_guardrails(func):
    """
    Decorator to apply guardrails to functions.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        guardrails = LanguageGuardrails()
        
        # Apply rate limiting
        rate_ok, rate_msg = guardrails.rate_limit(kwargs.get('user_id', 'default'))
        if not rate_ok:
            raise ValueError(rate_msg)
            
        # If text content is provided, validate it
        if 'text' in kwargs:
            # Validate language if specified
            if 'language' in kwargs:
                lang_ok, lang_msg = guardrails.validate_language(
                    kwargs['text'], 
                    kwargs['language']
                )
                if not lang_ok:
                    raise ValueError(lang_msg)
            
            # Check content safety
            safety_ok, safety_msg = guardrails.check_content_safety(kwargs['text'])
            if not safety_ok:
                raise ValueError(safety_msg)
        
        # If audio duration is provided, validate it
        if 'audio_duration' in kwargs:
            audio_ok, audio_msg = guardrails.validate_audio_length(
                kwargs['audio_duration']
            )
            if not audio_ok:
                raise ValueError(audio_msg)
        
        return func(self, *args, **kwargs)
    
    return wrapper
