"""
Intent Router - Routing based on VNPTAI_INTENT_CLASSIFIER
NO rule-based fallback, purely ML-based classification
"""
from typing import Dict, List, Optional
import re


class IntentRouter:
    """
    Route queries based on VNPTAI_INTENT_CLASSIFIER output
    NO rule-based fallback - chỉ dùng VNPTAI classifier
    """
    
    def __init__(self, model_path: str = "./models/intent/complex_dual_task"):
        """
        Args:
            model_path: Path to VNPTAI_INTENT_CLASSIFIER_BASE model
        """
        from src.rag.intention import VNPTAI_INTENT_CLASSIFIER_BASE
        self.intent_classifier = VNPTAI_INTENT_CLASSIFIER_BASE(model_path=model_path)
    
    def route(self, query: str) -> Dict:
        """
        Main routing logic based on category and complexity scores
        """
        # 1. Run VNPTAI classifier
        result = self.intent_classifier.scan(query)
        category = result['category']
        complexity = result['complexity']
        
        # 2. Check embedded knowledge in query (PRIORITY 1)
        has_embedded = self._check_embedded_knowledge(query)
        
        if has_embedded:
             return {
                'strategy': 'embedded_context',
                'category': 'ReadingComprehension', # Override category
                'complexity': complexity,
                'tools': ['use_embedded_context'],
                'metadata': {'skip_rag': True},
                'probs': result.get('category_probs', {})
            }

        # 3. Heuristic for "Fill in the blank" / "Idioms" (PRIORITY 2)
        # These are often misclassified as MathLogic or Physics
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["điền từ", "còn thiếu", "thành ngữ", "tục ngữ", "ca dao"]):
             return {
                'strategy': 'rag',
                'category': 'General', # Override to General
                'complexity': complexity,
                'tools': ['search_knowledge_base'],
                'metadata': {'top_k': 20, 'min_score': 0.6},
                'probs': result.get('category_probs', {})
            }

        # 4. Standard Routing
        if category == 'Refusal':
             return {
                'strategy': 'refusal',
                'category': category,
                'complexity': complexity,
                'tools': [],
                'metadata': {'requires_refusal_prompt': True},
                'probs': result.get('category_probs', {})
            }
        
        elif category == 'MathLogic':
            problem_type = self._detect_problem_type(query)
            # If problem_type is 'logic' (default), it might just be reasoning, not deep math
            return {
                'strategy': 'cot',
                'category': category,
                'complexity': complexity,
                'tools': ['solve_math_problem'],
                'metadata': {
                    'use_verification': True,
                    'problem_type': problem_type
                },
                'probs': result.get('category_probs', {})
            }
        
        elif category == 'Correctness':
            # Domain knowledge dominant → CoT (math/science)
            # But ONLY if it looks like a math/science problem
            problem_type = self._detect_problem_type(query)
            
            is_math_science = problem_type not in ['logic', 'unknown']
            
            if complexity['domain_knowledge'] > complexity['contextual_knowledge'] and is_math_science:
                return {
                    'strategy': 'cot',
                    'category': category,
                    'complexity': complexity,
                    'tools': ['solve_math_problem'],
                    'metadata': {
                        'use_verification': True,
                        'problem_type': problem_type
                    },
                    'probs': result.get('category_probs', {})
                }
            # Contextual knowledge dominant → RAG
            else:
                return {
                    'strategy': 'rag',
                    'category': category,
                    'complexity': complexity,
                    'tools': ['search_knowledge_base'],
                    'metadata': {'top_k': 20},
                    'probs': result.get('category_probs', {})
                }
        
        elif category == 'LongContext':
             return {
                'strategy': 'rag',
                'category': category,
                'complexity': complexity,
                'tools': ['search_knowledge_base'],
                'metadata': {'top_k': 20},
                'probs': result.get('category_probs', {})
            }
        
        else:  # General, NeutralPOV
            # SPECIAL CASE: Classifier says General but Refusal prob is significant (> 0.2)
            # This handles "borderline" queries like "How to fake labels?"
            refusal_prob = result['category_probs'].get('Refusal', 0.0)
            
            if category == 'General' and refusal_prob > 0.1:
                 # Check for explicit refusal triggers or unsafe patterns
                 # Re-use the unsafe keywords list or check "I cannot answer" in potential output scenario
                 unsafe_patterns = [
                    "làm giả", "tránh bị phát hiện", "qua mặt", "trốn", "không thể trả lời"
                 ]
                 if any(kw in query.lower() for kw in unsafe_patterns):
                      return {
                        'strategy': 'refusal',
                        'category': 'Refusal', # Force Refusal
                        'complexity': complexity,
                        'tools': [],
                        'metadata': {
                            'requires_refusal_prompt': True, 
                            'reason': 'general_with_high_refusal_prob'
                        },
                        'probs': result.get('category_probs', {})
                    }

            # Updated: Enable RAG with strict threshold for general queries
            return {
                'strategy': 'rag',
                'category': category,
                'complexity': complexity,
                'tools': ['search_knowledge_base'],
                'metadata': {
                    'top_k': 20,
                    'min_score': 0.65
                },
                'probs': result.get('category_probs', {})
            }
    
    def _check_embedded_knowledge(self, query: str) -> bool:
        """Check if query already contains context/knowledge"""
        indicators = [
            r'dựa trên', r'theo thông tin', r'như đã nêu',
            r'trong đoạn văn', r'theo đoạn', r'căn cứ vào',
            r'\[1\]', r'\[2\]', r'Tiêu đề:', r'Nội dung:',
            r'Đoạn thông tin', r'Context:'
        ]
        query_lower = query.lower()
        return any(re.search(ind, query_lower) for ind in indicators)
    
    def _detect_problem_type(self, query: str) -> str:
        """Detect specific problem type for better prompting"""
        query_lower = query.lower()
        
        # Economics (Stricter keywords)
        if any(kw in query_lower for kw in [
            'co giãn', 'elasticity', 'lãi suất', 'interest', 
            'chi phí biên', 'marginal cost', 'cầu kéo', 'cung tiền', 
            'gdp', 'lạm phát' # Removed generic "giá", "cung", "cầu"
        ]):
            return 'economics'
        
        # Statistics
        if any(kw in query_lower for kw in [
            'kiểm định', 'hypothesis', 't-test', 'z-test',
            'trung bình mẫu', 'phương sai', 'độ lệch chuẩn',
            'p-value', 'chi-square', 'hồi quy' # Stricter phrases
        ]):
            return 'statistics'
        
        # Calculus
        if any(kw in query_lower for kw in [
            'đạo hàm', 'tích phân', 'giới hạn của', 'lim x',
            'cực trị', 'điểm uốn', 'vi phân', 'nguyên hàm'
        ]):
            return 'calculus'
        
        # Physics (Stricter)
        if any(kw in query_lower for kw in [
            'vận tốc', 'gia tốc', 'động năng', 'thế năng',
            'dao động điều hòa', 'bước sóng', 'tần số góc', 'cường độ dòng điện',
            'hạt nhân', 'phóng xạ', 'nhiệt lượng' # Removed single words "lực", "sóng", "điện"
        ]):
            return 'physics'
        
        # Chemistry
        if any(kw in query_lower for kw in [
            'phản ứng hóa học', 'số mol', 'nồng độ mol', 'oxi hóa khử',
            'nguyên tử khối', 'phân tử khối', 'cân bằng phương trình'
        ]):
            return 'chemistry'
        
        # Default fallback
        # If it contains numbers or equations -> math
        # Else -> logic
        if re.search(r'\d+', query) or re.search(r'[=+\-*/^]', query):
             return 'math'
             
        return 'logic'


if __name__ == "__main__":
    # Test router
    router = IntentRouter()
    
    test_queries = [
        "Tính đạo hàm của y = x^2 + 3x",
        "Lãi suất 10% bán niên, lãi suất hiệu quả hàng năm?",
        "Nghị định 68/2019 quy định gì?",
        "Xin chào, bạn khỏe không?"
    ]
    
    for q in test_queries:
        result = router.route(q)
        print(f"\n📝 Query: {q[:50]}...")
        print(f"   Strategy: {result['strategy']}")
        print(f"   Tools: {result['tools']}")
        print(f"   Problem type: {result['metadata'].get('problem_type', 'N/A')}")
