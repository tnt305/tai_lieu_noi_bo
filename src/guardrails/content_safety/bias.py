"""
Bias Detection - Phát hiện thành kiến (Vietnamese support)

Categories:
- Gender bias
- Racial/ethnic bias
- Age bias
- Social class bias
"""
import re
from typing import Tuple, List, Set, Dict

from ..base import Scanner


class VietnameseBiasKeywords:
    """Vietnamese bias keywords by category"""
    
    # Gender bias
    gender_bias = {
        # Stereotypes về phụ nữ
        'đàn bà', 'con gái', 'phụ nữ yếu đuối', 'đàn bà nói nhiều',
        'việc đàn bà', 'đứa con gái', 'mẹ thiên hạ',
        # Stereotypes về đàn ông
        'đàn ông phải', 'con trai phải', 'đàn ông không được khóc',
        'đàn ông mạnh mẽ', 'con trai không nhõng nhẽo',
    }
    
    # Racial/ethnic bias
    racial_bias = {
        # Xúc phạm sắc tộc
        'mọi', 'rợ', 'thổ dân', 'dân tộc thiểu số kém',
        'người da đen', 'người da trắng hơn',
        # Regional bias
        'miền nam', 'miền bắc', 'miền trung kém',
        'người quê', 'thằng quê', 'dân quê',
    }
    
    # Age bias
    age_bias = {
        'già rồi', 'quá già', 'hết tuổi', 'thời đại cũ',
        'trẻ con không biết gì', 'trẻ con còn non nớt',
        'già cổ lỗ sĩ', 'ông già bà già',
    }
    
    # Social class bias
    class_bias = {
        'người nghèo', 'nghèo khó', 'thấp kém', 'hạ đẳng',
        'gái quê', 'dân nghèo', 'người nghèo không học hành',
        'không có học', 'không biết chữ',
    }
    
    @classmethod
    def get_all_keywords(cls) -> Set[str]:
        """Get all bias keywords"""
        return cls.gender_bias | cls.racial_bias | cls.age_bias | cls.class_bias
    
    @classmethod
    def get_by_category(cls, category: str) -> Set[str]:
        """Get keywords by category"""
        categories = {
            'gender': cls.gender_bias,
            'racial': cls.racial_bias,
            'age': cls.age_bias,
            'class': cls.class_bias,
        }
        return categories.get(category, set())


class BiasScanner(Scanner):
    """
    Bias Scanner - Phát hiện thành kiến (Vietnamese)
    
    Detects:
    - Gender bias (nam/nữ)
    - Racial/ethnic bias (sắc tộc, vùng miền)
    - Age bias (tuổi tác)
    - Social class bias (giai tầng)
    """
    
    def __init__(self, threshold: float = 0.3, categories: List[str] = None):
        """
        Khởi tạo bias scanner.
        
        Args:
            threshold: Ngưỡng bias (0-1)
            categories: Danh sách categories cần detect
        """
        self._threshold = threshold
        
        # Get keywords
        if categories:
            self._keywords = set()
            for cat in categories:
                self._keywords.update(VietnameseBiasKeywords.get_by_category(cat))
        else:
            self._keywords = VietnameseBiasKeywords.get_all_keywords()
        
        # Create regex pattern
        if self._keywords:
            pattern_str = r'\b(?:' + '|'.join(re.escape(kw) for kw in self._keywords) + r')\b'
            self._pattern = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
        else:
            self._pattern = None
    
    def scan(self, prompt: str) -> Tuple[str, bool, float]:
        """
        Quét bias content.
        
        Returns:
            - sanitized_text: Original text
            - is_valid: True nếu không bias, False nếu bias
            - risk_score: Tỷ lệ bias (0-1)
        """
        if not prompt or prompt.strip() == "":
            return prompt, True, 0.0
        
        if not self._pattern:
            return prompt, True, 0.0
        
        # Find all bias phrases
        matches = list(self._pattern.finditer(prompt))
        
        if not matches:
            return prompt, True, 0.0
        
        # Calculate bias score
        words = prompt.split()
        bias_count = len(matches)
        total_words = len(words)
        
        if total_words == 0:
            bias_score = 0.0
        else:
            bias_score = min(1.0, bias_count / total_words * 3)
        
        is_valid = bias_score < self._threshold
        
        # Extract bias phrases
        bias_phrases = [match.group(0) for match in matches]
        
        if not is_valid:
            print(f"⚠️  Bias detected (score={bias_score:.2f}): {', '.join(set(bias_phrases[:3]))}")
        
        return prompt, is_valid, bias_score
