"""
Language Detection - Phát hiện ngôn ngữ
Chỉ cho phép tiếng Việt
"""
import re
from typing import Tuple, List

from ..base import Scanner


class VietnameseLanguageDetector:
    """Simple Vietnamese language detector using character patterns"""
    
    # Vietnamese diacritics
    vietnamese_chars = set('àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ')
    vietnamese_chars.update('ÀÁẢÃẠÂẦẤẨẪẬĂẰẮẲẴẶÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ')
    
    # Common Vietnamese words
    common_vietnamese_words = {
        'và', 'là', 'của', 'có', 'trong', 'được', 'với', 'cho', 'để', 'này',
        'những', 'các', 'người', 'không', 'một', 'từ', 'về', 'được', 'đã', 'sẽ',
        'tôi', 'bạn', 'chúng tôi', 'họ', 'nó', 'mình', 'gì', 'như', 'vì', 'còn',
    }
    
    # English common words (for filtering)
    english_words = {
        'the', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'in', 'on',
        'at', 'to', 'for', 'with', 'from', 'by', 'of', 'a', 'an', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    }
    
    @classmethod
    def detect(cls, text: str) -> Tuple[str, float]:
        """
        Detect language of text.
        
        Returns:
            - language: 'vi' or 'other'
            - confidence: 0-1
        """
        if not text or len(text.strip()) == 0:
            return 'unknown', 0.0
        
        text_lower = text.lower()
        
        # Method 1: Vietnamese diacritics
        vietnamese_char_count = sum(1 for char in text if char in cls.vietnamese_chars)
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return 'unknown', 0.0
        
        diacritic_ratio = vietnamese_char_count / total_chars
        
        # Method 2: Common Vietnamese words
        words = text_lower.split()
        vietnamese_word_count = sum(1 for word in words if word in cls.common_vietnamese_words)
        english_word_count = sum(1 for word in words if word in cls.english_words)
        
        total_words = len(words)
        if total_words == 0:
            return 'unknown', 0.0
        
        vietnamese_word_ratio = vietnamese_word_count / total_words
        english_word_ratio = english_word_count / total_words
        
        # Combine signals
        # If has Vietnamese diacritics OR Vietnamese words, likely Vietnamese
        confidence = max(diacritic_ratio * 2, vietnamese_word_ratio)
        
        # If has more English words, likely English
        if english_word_ratio > vietnamese_word_ratio and english_word_ratio > 0.3:
            return 'other', 1.0 - confidence
        
        # Decision
        if confidence > 0.3:
            return 'vi', confidence
        else:
            return 'other', 1.0 - confidence


class LanguageScanner(Scanner):
    """
    Language Scanner - Chỉ cho phép tiếng Việt
    
    Automatically detects language and blocks non-Vietnamese text.
    """
    
    def __init__(self, allowed_languages: List[str] = None, threshold: float = 0.2):
        """
        Khởi tạo language scanner.
        
        Args:
            allowed_languages: Danh sách ngôn ngữ cho phép (default: ['vi'])
            threshold: Ngưỡng confidence (0-1)
        """
        self._allowed_languages = allowed_languages or ['vi']
        self._threshold = threshold
    
    def scan(self, prompt: str) -> Tuple[str, bool, float]:
        """
        Kiểm tra ngôn ngữ.
        
        Returns:
            - sanitized_text: Original text
            - is_valid: True nếu là tiếng Việt, False nếu không
            - risk_score: 1 - confidence (risk of wrong language)
        """
        if not prompt or prompt.strip() == "":
            return prompt, True, 0.0
        
        # Detect language
        language, confidence = VietnameseLanguageDetector.detect(prompt)
        
        # Check if allowed
        is_valid = language in self._allowed_languages and confidence >= self._threshold
        
        # Risk score: 1 if wrong language, 0 if correct
        risk_score = 0.0 if is_valid else 1.0
        
        if not is_valid:
            print(f"⚠️  Wrong language detected: {language} (confidence={confidence:.2f})")
            print(f"   Only {self._allowed_languages} allowed")
        
        return prompt, is_valid, risk_score
