import logging
import boto3
import botocore.config
import os
from typing import Dict

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
    
    def _convert_with_mapping(self, text: str) -> str:
        """Convert Hindi to Urdu using character mapping."""
        try:
            # Convert text character by character
            urdu_text = ''
            i = 0
            while i < len(text):
                # Handle special cases for combined characters
                if i + 1 < len(text) and text[i:i+2] in self._script_map:
                    urdu_text += self._script_map[text[i:i+2]]
                    i += 2
                elif text[i] in self._script_map:
                    urdu_text += self._script_map[text[i]]
                    i += 1
                else:
                    urdu_text += text[i]
                    i += 1
            
            # Post-processing fixes
            urdu_text = urdu_text.replace('  ', ' ')  # Remove double spaces
            urdu_text = urdu_text.strip()  # Remove leading/trailing spaces
            
            return urdu_text
            
        except Exception as e:
            logger.error(f"Error in character mapping conversion: {e}")
            return text
    
    def convert_hindi_to_urdu(self, text: str) -> str:
        """Convert Hindi text to Urdu script using AWS Translate with fallback."""
        try:
            # Skip if text is empty or already in Urdu script
            if not text or any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text):
                return text
            
            # Try AWS Translate first
            if self._translate:
                try:
                    response = self._translate.translate_text(
                        Text=text,
                        SourceLanguageCode='hi',
                        TargetLanguageCode='ur'
                    )
                    translated_text = response['TranslatedText']
                    logger.info("Successfully used AWS Translate for conversion")
                    return translated_text
                except Exception as e:
                    logger.warning(f"AWS Translate failed, falling back to character mapping: {e}")
            
            # Fallback to character mapping
            return self._convert_with_mapping(text)
            
        except Exception as e:
            logger.error(f"Error converting Hindi to Urdu: {e}")
            return text  # Return original text if conversion fails
