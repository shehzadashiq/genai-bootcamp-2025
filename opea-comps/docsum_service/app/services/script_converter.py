import logging
from typing import Dict
import re

logger = logging.getLogger(__name__)

class ScriptConverter:
    def __init__(self):
        # Initialize character mappings
        self.urdu_to_dev = {
            # Basic letters
            'ا': 'अ',
            'آ': 'आ',
            'ب': 'ब',
            'پ': 'प',
            'ت': 'त',
            'ٹ': 'ट',
            'ث': 'स',
            'ج': 'ज',
            'چ': 'च',
            'ح': 'ह',
            'خ': 'ख़',
            'د': 'द',
            'ڈ': 'ड',
            'ذ': 'ज़',
            'ر': 'र',
            'ڑ': 'ड़',
            'ز': 'ज़',
            'ژ': 'झ़',
            'س': 'स',
            'ش': 'श',
            'ص': 'स',
            'ض': 'ज़',
            'ط': 'त',
            'ظ': 'ज़',
            'ع': 'अ',
            'غ': 'ग़',
            'ف': '__F__',  # Special marker for F sound
            'ق': 'क़',
            'ک': 'क',
            'گ': 'ग',
            'ل': 'ल',
            'م': 'म',
            'ن': 'न',
            'ں': 'ं',
            'و': 'व',
            'ہ': 'ह',
            'ھ': 'ह',
            'ء': 'अ',
            'ی': 'य',
            'ے': 'े',
            
            # Vowel marks
            'َ': 'ा',  # zabar
            'ِ': 'ि',  # zer
            'ُ': 'ु',  # pesh
            '٘': '्',  # jazm
            'ٰ': 'ा',  # alif maqsura
            'ٖ': 'ी',  # choti ye
            'ٗ': 'ु',  # ulta pesh
            
            # Numbers
            '۰': '०',
            '۱': '१',
            '۲': '२',
            '۳': '३',
            '۴': '४',
            '۵': '५',
            '۶': '६',
            '۷': '७',
            '८': '८',
            '۹': '९',
            
            # Punctuation
            '۔': '।',
            '؟': '?',
            '،': ',',
        }
        
        # Special combinations
        self.special_combinations = {
            'ئ': 'य',
            'ؤ': 'व',
            'اے': 'ए',
            'او': 'ओ',
            'ای': 'ई',
            'آئ': 'आई',
            'یا': 'या',
            'کی': 'की',
            'کے': 'के',
            'کا': 'का',
            'کو': 'को',
            'کر': 'कर',
            'نے': 'ने',
            'سے': 'से',
            'مے': 'मे',
            'پر': 'पर',
        }
        
        # Define consonant pattern
        self.consonants = '[कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह]'
        self.vowel_marks = '[ािीुूृेैोौंःँ्]'
        
        logger.info("Script converter initialized")
    
    def convert_to_devanagari(self, text: str) -> str:
        """Convert Urdu text to Devanagari script while preserving pronunciation."""
        try:
            # First handle special combinations
            for urdu, dev in self.special_combinations.items():
                text = text.replace(urdu, dev)
            
            # Convert remaining characters
            result = ""
            i = 0
            while i < len(text):
                if i + 1 < len(text) and text[i:i+2] in self.special_combinations:
                    result += self.special_combinations[text[i:i+2]]
                    i += 2
                else:
                    char = text[i]
                    result += self.urdu_to_dev.get(char, char)
                    i += 1
            
            # Post-processing fixes
            result = self._post_process(result)
            
            logger.info("Successfully converted text to Devanagari")
            return result
            
        except Exception as e:
            logger.error(f"Error converting script: {str(e)}")
            raise
    
    def _post_process(self, text: str) -> str:
        """Apply post-processing fixes for better pronunciation."""
        try:
            # Add inherent 'a' vowel where needed
            text = re.sub(f"({self.consonants})(?!{self.vowel_marks})", r'\1अ', text)
            
            # Fix common pronunciation patterns
            replacements = [
                ('अय', 'ऐ'),  # Fix ai sound
                ('अव', 'औ'),  # Fix au sound
                (f"({self.consonants})्य", r'\1य'),  # Fix consonant + य
                (f"({self.consonants})्व", r'\1व'),  # Fix consonant + व
                ('्अ', ''),  # Remove unnecessary halant + a
            ]
            
            for pattern, replacement in replacements:
                text = text.replace(pattern, replacement)
            
            return text
            
        except Exception as e:
            logger.error(f"Error in post-processing: {str(e)}")
            raise
