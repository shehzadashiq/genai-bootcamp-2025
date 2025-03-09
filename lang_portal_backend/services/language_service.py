import logging
import boto3
import botocore.config
import os
from typing import Dict, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class LanguageService:
    _instance = None
    _translate = None
    
    # Hindi to Urdu script mapping for fallback
    _script_map = {
        # Vowels
        'अ': 'ا', 'आ': 'آ', 'इ': 'ا', 'ई': 'ای',
        'उ': 'ا', 'ऊ': 'او', 'ए': 'ے', 'ऐ': 'ای',
        'ओ': 'او', 'औ': 'او', 'ं': 'ں', 'ः': '',
        
        # Consonants
        'क': 'ک', 'ख': 'کھ', 'ग': 'گ', 'घ': 'گھ', 'ङ': 'نگ',
        'च': 'چ', 'छ': 'چھ', 'ज': 'ج', 'झ': 'جھ', 'ञ': 'نج',
        'ट': 'ٹ', 'ठ': 'ٹھ', 'ड': 'ڈ', 'ढ': 'ڈھ', 'ण': 'ن',
        'त': 'ت', 'थ': 'تھ', 'द': 'د', 'ध': 'دھ', 'न': 'ن',
        'प': 'پ', 'फ': 'پھ', 'ब': 'ب', 'भ': 'بھ', 'म': 'م',
        'य': 'ی', 'र': 'ر', 'ल': 'ل', 'व': 'و',
        'श': 'ش', 'ष': 'ش', 'स': 'س', 'ह': 'ہ',
        
        # Matras (vowel signs)
        'ा': 'ا', 'ि': 'ِ', 'ी': 'ی',
        'ु': 'ُ', 'ू': 'و', 'े': 'ے',
        'ै': 'ے', 'ो': 'و', 'ौ': 'و',
        '्': '',  # Halant
        
        # Numerals
        '०': '٠', '१': '١', '२': '٢', '३': '٣', '४': '٤',
        '५': '٥', '६': '٦', '७': '٧', '८': '٨', '९': '٩',
        
        # Punctuation
        '।': '۔', '॥': '۔',
        
        # Common combined characters
        'क्ष': 'کش', 'त्र': 'تر', 'ज्ञ': 'گی',
        'श्र': 'شر', 'क्र': 'کر', 'फ्र': 'فر',
    }
    
    # Special case handling for combined characters
    _combined_chars = {
        'क्क': 'کّ', 'क्ख': 'कّھ', 'क्त': 'کت',
        'त्त': 'تّ', 'त्र': 'تر', 'द्द': 'दّ',
        'द्ध': 'दّھ', 'प्प': 'पّ', 'र्र': 'रّ',
        'ल्ल': 'ल्ल', 'ज्ज': 'ज्ज', 'श्श': 'श्श'
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageService, cls).__new__(cls)
            try:
                # Initialize AWS Translate client
                config = botocore.config.Config(
                    region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                    retries={'max_attempts': 3}
                )
                cls._translate = boto3.client(
                    'translate',
                    config=config,
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
                )
                logger.info("AWS Translate client initialized successfully")
            except Exception as e:
                logger.error(f"AWS Translate initialization failed: {e}")
                cls._translate = None
        return cls._instance
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better conversion."""
        # Remove extra spaces
        text = ' '.join(text.split())
        
        # Normalize Arabic/Persian characters to Urdu
        replacements = {
            'ي': 'ی',  # Arabic Ya to Urdu Ya
            'ك': 'ک',  # Arabic Kaf to Urdu Kaf
            'ە': 'ہ',  # Arabic Ha to Urdu Ha
            '۰': '٠',  # Normalize numerals
            '۱': '١',
            '۲': '٢',
            '۳': '٣',
            '۴': '٤',
            '۵': '٥',
            '۶': '٦',
            '۷': '٧',
            '۸': '٨',
            '۹': '٩',
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        
        return text
    
    def _detect_script(self, text: str) -> Tuple[str, float]:
        """
        Detect if text is in Hindi, Urdu, or other script.
        Returns tuple of (script_code, confidence)
        """
        # Count characters in different Unicode ranges
        urdu_count = sum(1 for c in text if 0x0600 <= ord(c) <= 0x06FF)
        hindi_count = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F)
        total_chars = len(''.join(text.split()))  # Count non-space characters
        
        if total_chars == 0:
            return ('unknown', 0.0)
        
        urdu_ratio = urdu_count / total_chars
        hindi_ratio = hindi_count / total_chars
        
        if urdu_ratio > 0.5:
            return ('ur', urdu_ratio)
        elif hindi_ratio > 0.5:
            return ('hi', hindi_ratio)
        return ('other', max(urdu_ratio, hindi_ratio))
    
    def _convert_with_mapping(self, text: str) -> str:
        """Convert Hindi to Urdu using character mapping."""
        try:
            # Convert text character by character
            urdu_text = ''
            i = 0
            while i < len(text):
                # Try combined characters first
                found_combined = False
                for length in range(3, 0, -1):  # Try 3, 2, then 1 character combinations
                    if i + length <= len(text):
                        chunk = text[i:i+length]
                        if chunk in self._combined_chars:
                            urdu_text += self._combined_chars[chunk]
                            i += length
                            found_combined = True
                            break
                        elif chunk in self._script_map:
                            urdu_text += self._script_map[chunk]
                            i += length
                            found_combined = True
                            break
                
                if not found_combined:
                    if text[i] in self._script_map:
                        urdu_text += self._script_map[text[i]]
                    else:
                        urdu_text += text[i]
                    i += 1
            
            # Normalize the converted text
            urdu_text = self._normalize_text(urdu_text)
            
            return urdu_text
            
        except Exception as e:
            logger.error(f"Error in character mapping conversion: {e}")
            return text
    
    def convert_hindi_to_urdu(self, text: str) -> str:
        """Convert Hindi text to Urdu script using AWS Translate with fallback."""
        try:
            # Skip if text is empty
            if not text:
                return text
            
            # Detect script and confidence
            script, confidence = self._detect_script(text)
            logger.debug(f"Detected script: {script} with confidence: {confidence:.2f}")
            
            # If already in Urdu with high confidence, just normalize
            if script == 'ur' and confidence > 0.8:
                return self._normalize_text(text)
            
            # If not Hindi, return as is
            if script != 'hi' and script != 'unknown':
                return text
            
            # Try AWS Translate first
            if self._translate:
                try:
                    response = self._translate.translate_text(
                        Text=text,
                        SourceLanguageCode='hi',
                        TargetLanguageCode='ur'
                    )
                    translated_text = self._normalize_text(response['TranslatedText'])
                    logger.info("Successfully used AWS Translate for conversion")
                    return translated_text
                except Exception as e:
                    logger.warning(f"AWS Translate failed, falling back to character mapping: {e}")
            
            # Fallback to character mapping
            logger.info("Using character mapping fallback")
            return self._convert_with_mapping(text)
            
        except Exception as e:
            logger.error(f"Error converting Hindi to Urdu: {e}")
            return text  # Return original text if conversion fails
