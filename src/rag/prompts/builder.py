"""
Domain-Specific Prompt Builder for MathSolver
NO LLM CALL - Only builds prompts for Large LLM
"""
from typing import Dict, List, Optional
from .templates import *  

class MathPromptBuilder:
    """
    Build domain-specific prompts for math/science problems
    DOES NOT call LLM - returns prompt string only
    """
    
    # Domain-specific system prompts
    DOMAIN_PROMPTS = {
        "economics": ECONOMICS,
        "statistics": STATISTIC,
        "calculus": CALCULUS,
        "physics": PHYSICS,
        "chemistry": CHEMISTRY,
        "logic": LOGICAL,
        "math": MATHEMATICS,
    }
    
    def build_messages(
        self,
        problem_statement: str,
        problem_type: str = "math",
        given_options: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Build structured messages for Chat Completion API
        
        Args:
            problem_statement: Bài toán
            problem_type: Loại bài (economics, physics, etc.)
            given_options: Các phương án trắc nghiệm
        
        Returns:
            List[Dict]: List of messages [{"role": "system", ...}, ...]
        """
        from .few_shot_examples import EXAMPLE_MAP
        
        # 1. Get Base System Prompt
        type_names = {
            "economics": "kinh tế",
            "statistics": "thống kê", 
            "calculus": "giải tích",
            "physics": "vật lý",
            "chemistry": "hóa học",
            "logic": "logic",
            "math": "toán học"
        }
        context = type_names.get(problem_type, "khoa học")
        
        system_instruction = f"""Bạn là trợ lý AI chuyên giải bài tập {context.upper()}. 
Áp dụng các kỹ thuật sau để giải quyết vấn đề (tránh over-complex):
- Systematic Reasoning (tính trực tiếp, không diễn giải dài)
- Equation-Based Reasoning (lập hệ, lập phương trình)
- Pattern / Structure Recognition (nhận dạng mẫu)
- Transform-Based Reasoning (đổi biến, chuẩn hóa)
- Solution Templates theo chủ đề (tổ hợp, hình học, bất đẳng thức…)
- Symbolic Simplification (rút gọn đại số kiểu CAS)
- Graphical / Geometric Reasoning
- Local–Global Reasoning
- Heuristic (thử giá trị, đặt cận)

**Yêu cầu khi giải:**
1. Chọn đúng phương pháp phù hợp nhất với cấu trúc bài → *nêu tên phương pháp ở đầu* (không cần giải thích dài).  
2. Trình bày lời giải gọn, chính xác, workflow rõ ràng dạng markdown:  
   - Tóm tắt dữ kiện  
   - Thiết lập mô hình/biểu thức  
   - Giải quyết logic  
   - Kết luận cuối  
3. Chỉ dùng CoT khi đó là cách hiệu quả nhất.  
4. Luôn kiểm tra lại kết quả cuối bằng bước xác minh ngắn.

QUY TẮC BẮT BUỘC:
- Luôn sử dụng LaTeX chuẩn cho công thức toán (VD: $\\frac{{a}}{{b}}$ thay vì rac{{a}}{{b}}).
- output JSON ở bước cuối cùng: {{"answer": "<nội dung đúng>"}}.
- Không được đưa ra đáp án dạng trắc nghiệm A, B, C, D trong JSON, chỉ đưa nội dung."""

        messages = [
            {"role": "system", "content": system_instruction}
        ]
        
        # 2. Add Few-Shot Examples (Dynamic based on type)
        # Select examples for current problem type (fallback to math)
        examples = EXAMPLE_MAP.get(problem_type, EXAMPLE_MAP["math"])
        
        # Pick up to 2 examples
        for ex in examples[:2]:
            messages.append({"role": "user", "content": f"Đề bài: {ex['question']}"})
            messages.append({"role": "assistant", "content": ex['answer']})
            
        # 3. Add User Problem
        real_user_content = f"ĐỀ BÀI:\n{problem_statement}"
        
        messages.append({"role": "user", "content": real_user_content})
        
        return messages

    # Deprecated string-based method
    def build_prompt(self, *args, **kwargs):
        raise NotImplementedError("Use build_messages() instead for structured chat prompting.")

    # Deprecated wrapper
    def solve(self, *args, **kwargs):
        raise NotImplementedError("Use build_messages() in Orchestrator.")


if __name__ == "__main__":
    # Test prompt builder
    builder = MathPromptBuilder()
    
    # Test economics
    print("=" * 60)
    print("ECONOMICS PROMPT:")
    print("=" * 60)
    prompt = builder.build_prompt(
        "Lãi suất danh nghĩa 10% bán niên, tính lãi suất hiệu quả hàng năm?",
        problem_type="economics",
        given_options=["10%", "10.25%", "10.5%", "11%"]
    )
    print(prompt[:500] + "...")
    
    # Test physics
    print("\n" + "=" * 60)
    print("PHYSICS PROMPT:")
    print("=" * 60)
    prompt = builder.build_prompt(
        "Một vật rơi tự do từ độ cao h=10m. Tính vận tốc khi chạm đất (g=10m/s²)",
        problem_type="physics"
    )
    print(prompt[:500] + "...")
