"""
Hindi to Urdu script conversion implementation.
Provides character mapping and text normalization for Hindi to Urdu conversion.
"""
from typing import Dict, List, Optional, Tuple
import re

class HindiUrduConverter:
    def __init__(self):
        # Basic character mappings
        self.CHAR_MAP = {
            # Vowels
            'अ': 'ا',
            'आ': 'آ',
            'इ': 'ا',
            'ई': 'ای',
            'उ': 'ا',
            'ऊ': 'او',
            'ए': 'ے',
            'ऐ': 'ـے',
            'ओ': 'و',
            'औ': 'او',
            
            # Consonants
            'क': 'ک',
            'ख': 'کھ',
            'ग': 'گ',
            'घ': 'گھ',
            'ङ': 'نگ',
            'च': 'چ',
            'छ': 'چھ',
            'ज': 'ج',
            'झ': 'جھ',
            'ञ': 'نج',
            'ट': 'ٹ',
            'ठ': 'ٹھ',
            'ड': 'ڈ',
            'ढ': 'ڈھ',
            'ण': 'ن',
            'त': 'ت',
            'थ': 'تھ',
            'द': 'د',
            'ध': 'دھ',
            'न': 'ن',
            'प': 'پ',
            'फ': 'پھ',
            'ब': 'ب',
            'भ': 'بھ',
            'म': 'م',
            'य': 'ی',
            'र': 'ر',
            'ल': 'ل',
            'व': 'و',
            'श': 'ش',
            'ष': 'ش',
            'स': 'س',
            'ह': 'ہ',
            
            # Matras (vowel signs)
            'ा': 'ا',
            'ि': 'ِ',
            'ी': 'ی',
            'ु': 'ُ',
            'ू': 'و',
            'े': 'ے',
            'ै': 'ـے',
            'ो': 'و',
            'ौ': 'و',
            'ं': 'ں',
            'ँ': 'ں',
            
            # Numerals
            '०': '٠',
            '१': '١',
            '२': '٢',
            '३': '٣',
            '४': '٤',
            '५': '٥',
            '६': '٦',
            '७': '٧',
            '८': '٨',
            '९': '٩',
            
            # Punctuation
            '।': '۔',
            '॥': '۔',
            '?': '؟',
            ',': '،'
        }
        
        # Special combined character mappings
        self.COMBINED_CHARS = {
            'क्ष': 'کش',
            'त्र': 'تر',
            'ज्ञ': 'گی',
            'श्र': 'شر'
        }
        
        # Arabic/Persian to Urdu normalization
        self.NORMALIZE_CHARS = {
            'ك': 'ک',
            'ي': 'ی',
            'ى': 'ی',
            'ہ': 'ھ',
            '۰': '٠',
            '۱': '١',
            '۲': '٢',
            '۳': '٣',
            '۴': '٤',
            '۵': '٥',
            '۶': '٦',
            '۷': '٧',
            '۸': '٨',
            '۹': '٩'
        }

    def convert(self, text: str) -> str:
        """
        Convert Hindi text to Urdu script using character mapping system.
        Includes special case handling and text normalization.
        """
        # Step 1: Handle combined characters first
        for hindi, urdu in self.COMBINED_CHARS.items():
            text = text.replace(hindi, urdu)
        
        # Step 2: Convert basic characters
        result = ''
        i = 0
        while i < len(text):
            if text[i] in self.CHAR_MAP:
                result += self.CHAR_MAP[text[i]]
            else:
                result += text[i]
            i += 1
        
        # Step 3: Post-processing fixes
        result = self._post_process(result)
        
        # Step 4: Normalize Arabic/Persian characters to Urdu
        result = self._normalize_text(result)
        
        return result

    def _post_process(self, text: str) -> str:
        """
        Apply post-processing fixes for common issues:
        - Handle proper word spacing
        - Fix character combinations
        - Adjust diacritics
        """
        # Fix multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix diacritic placement
        text = re.sub(r'([ِ ُ])\s+', r'\1', text)
        
        # Handle special cases where characters need to be combined
        text = text.replace('ا ِ', 'اِ')
        text = text.replace('ا ُ', 'اُ')
        
        # Fix common character sequence issues
        text = text.replace('یی', 'ئی')
        text = text.replace('یے', 'ئے')
        
        return text

    def _normalize_text(self, text: str) -> str:
        """
        Normalize Arabic/Persian characters to their Urdu equivalents.
        """
        for arabic, urdu in self.NORMALIZE_CHARS.items():
            text = text.replace(arabic, urdu)
        return text

    def validate_conversion(self, hindi_text: str, urdu_text: str) -> Tuple[bool, str]:
        """
        Validate the conversion by checking for common errors.
        """
        # Convert the Hindi text
        converted = self.convert(hindi_text)
        
        # Check if the conversion matches the expected Urdu text
        if converted != urdu_text:
            # Find where the mismatch occurs
            mismatch_pos = -1
            for i in range(min(len(converted), len(urdu_text))):
                if converted[i] != urdu_text[i]:
                    mismatch_pos = i
                    break
            
            if mismatch_pos != -1:
                return False, f"Conversion mismatch at position {mismatch_pos}"
            else:
                return False, "Length mismatch in conversion"
        
        return True, "Conversion validated successfully"
