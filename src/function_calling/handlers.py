"""
Handlers - Các class xử lý cụ thể cho từng loại tool
"""
from typing import Dict, List, Any, Optional
import requests
import json

from src import load_llm_config
from src.rag.retriever import VNPTAIRetriever


class MathSolver:
    """
    Handler cho việc giải toán học
    Sử dụng VNPT AI LLM để giải bài toán
    """
    
    def __init__(self, model_type: str = "large"):
        """
        Args:
            model_type: Loại model ("large", "small", etc.)
        """
        self.config = load_llm_config(model_type)
        from src.functional.constants import API_URL
        self.api_url = API_URL
        
    def solve(
        self, 
        problem_statement: str,
        problem_type: str = "math",
        given_options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Giải bài toán
        
        Args:
            problem_statement: Đề bài
            problem_type: Loại bài toán (math, physics, chemistry)
            given_options: Các lựa chọn (nếu là trắc nghiệm)
            
        Returns:
            Dict chứa answer và reasoning
        """
        # Build prompt
        prompt = self._build_prompt(problem_statement, problem_type, given_options)
        
        # Call LLM
        headers = {
            'Authorization': self.config['authorization'],
            'Token-id': self.config['tokenId'],
            'Token-key': self.config['tokenKey'],
            'Content-Type': 'application/json',
        }
        
        json_data = {
            'model': 'vnptai_hackathon_large',
            'messages': [{"role": "user", "content": prompt}],
            'temperature': 0.3,  # Thấp hơn cho toán học
            'top_p': 0.9,
            'top_k': 20,
            'n': 1,
            'max_completion_tokens': 512,
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=json_data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            # Extract answer
            content = result['choices'][0]['message']['content']
            
            # Parse JSON response if possible
            try:
                parsed = json.loads(content)
                return {
                    "answer": parsed.get("answer", content),
                    "reasoning": parsed.get("reasoning", ""),
                    "raw_response": content
                }
            except json.JSONDecodeError:
                return {
                    "answer": content,
                    "reasoning": "",
                    "raw_response": content
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "answer": None,
                "reasoning": ""
            }
    
    def _build_prompt(
        self, 
        problem: str, 
        problem_type: str,
        options: Optional[List[str]] = None
    ) -> str:
        """Xây dựng prompt cho LLM"""
        
        prompt_parts = []
        
        # Specialized system prompts cho từng loại bài toán
        system_prompts = {
            "economics": (
                "Bạn là chuyên gia kinh tế. Phương pháp giải:\n"
                "- Xác định đúng công thức (elasticity dùng midpoint method, lãi suất kép, chi phí biên...)\n"
                "- Tính toán từng bước với số liệu cụ thể\n"
                "- Giải thích ý nghĩa kinh tế của kết quả"
            ),
            "statistics": (
                "Bạn là chuyên gia thống kê. Phương pháp giải:\n"
                "- Xác định loại test (t-test, z-test, chi-square...)\n"
                "- Áp dụng công thức tương ứng: t = (x̄ - μ₀)/(s/√n), z = (x̄ - μ)/(σ/√n)...\n"
                "- Diễn giải kết quả trong ngữ cảnh"
            ),
            "calculus": (
                "Bạn là chuyên gia giải tích. Phương pháp giải:\n"
                "- Áp dụng quy tắc đạo hàm (chain rule, product rule, quotient rule)\n"
                "- Phân tích điểm tới hạn: f'(x)=0, f''(x) để tìm cực trị và điểm uốn\n"
                "- Kiểm tra miền xác định và giới hạn"
            ),
            "physics": (
                "Bạn là chuyên gia vật lý. Phương pháp giải:\n"
                "1. Xác định đại lượng cần tìm và đại lượng đã biết\n"
                "2. Chọn định luật/công thức phù hợp (động học, động lực, năng lượng, sóng...)\n"
                "3. Nếu có quan hệ tỉ lệ (∝), phân tích: A ∝ B^n → B tăng k lần thì A tăng k^n lần\n"
                "4. Kiểm tra đơn vị và các định luật bảo toàn (năng lượng, động lượng...)"
            ),
            "chemistry": (
                "Bạn là chuyên gia hóa học. Phương pháp giải:\n"
                "- Viết và cân bằng phương trình hóa học\n"
                "- Tính toán mol, khối lượng, nồng độ theo đúng tỉ lệ hóa học\n"
                "- Xác định số oxi hóa khi cần"
            ),
            "logic": (
                "Phương pháp reasoning logic:\n"
                "- Phân tích từng bước một cách có hệ thống\n"
                "- Loại trừ các trường hợp không hợp lý\n"
                "- Đưa ra kết luận dựa trên logic chặt chẽ"
            )
        }
        
        # Add specialized system prompt if available
        if problem_type in system_prompts:
            prompt_parts.append(system_prompts[problem_type])
            prompt_parts.append("")  # Blank line
        
        # Add problem type context
        type_context = {
            "math": "toán học",
            "physics": "vật lý", 
            "chemistry": "hóa học",
            "economics": "kinh tế",
            "statistics": "thống kê",
            "calculus": "giải tích",
            "logic": "logic"
        }
        context = type_context.get(problem_type, "khoa học")
        
        prompt_parts.append(f"Giải bài toán {context} sau:")
        prompt_parts.append(problem)
        
        # Add options if multiple choice
        if options:
            prompt_parts.append("\nLựa chọn:")
            for i, opt in enumerate(options, 1):
                prompt_parts.append(f"{i}. {opt}")
        
        # Add format instruction
        prompt_parts.append("\nTrả lời theo format JSON:")
        prompt_parts.append('{"answer": "<đáp án hoặc phương án>", "reasoning": "<lý do ngắn gọn>"}')
        
        return "\n".join(prompt_parts)


class RAGHandler:
    """
    Handler cho việc tra cứu thông tin từ RAG system
    """
    
    def __init__(
        self, 
        collection_name: str = "360_xinchao",
        embedder_model: str = "vnptai_hackathon_embedding"

    ):
        """
        Args:
            collection_name: Tên collection trong Qdrant
            embedder_model: Model để embed
        """
        self.retriever = VNPTAIRetriever(
            collection_name=collection_name,
            embedder_model=embedder_model
        )
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        doc_type: Optional[str] = None,
        min_score: float = 0.5
    ) -> Dict[str, Any]:
        """
        Tìm kiếm thông tin
        
        Args:
            query: Câu hỏi
            top_k: Số kết quả
            doc_type: Loại văn bản (optional)
            min_score: Ngưỡng điểm tương đồng
            
        Returns:
            Dict chứa results và formatted context
        """
        # Tìm kiếm
        results = self.retriever.search(
            query=query,
            top_k=top_k,
            min_score=min_score  # Sử dụng dynamic threshold
        )
        
        if not results:
            return {
                "found": False,
                "results": [],
                "context": "Không tìm thấy thông tin liên quan.",
                "message": "Không có dữ liệu phù hợp trong cơ sở dữ liệu."
            }
        
        # Format context
        context = self._format_context(results)
        
        return {
            "found": True,
            "results": results,
            "context": context,
            "num_results": len(results)
        }
    
    def _format_context(self, results: List[Dict]) -> str:
        """Format kết quả thành context string"""
        parts = []
        
        for i, result in enumerate(results, 1):
            meta = result['metadata']
            parts.append(
                f"[Nguồn {i}] {meta.get('doc_title', 'N/A')}\n"
                f"Điểm tương đồng: {result['score']}\n"
                f"Nội dung: {result['content']}\n"
                f"URL: {meta.get('source_url', 'N/A')}"
            )
        
        return "\n\n---\n\n".join(parts)


class Calculator:
    """
    Handler đơn giản cho các phép tính cơ bản
    """
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Tính toán biểu thức
        
        Args:
            expression: Biểu thức toán học (string)
            
        Returns:
            Dict chứa result
        """
        try:
            # WARNING: eval() không an toàn cho production!
            # Chỉ dùng cho demo hoặc cần validation kỹ hơn
            # Có thể dùng ast.literal_eval() hoặc sympyresult = eval(expression, {"__builtins__": {}}, {})
            
            # Safer approach: use allowed math functions
            import math
            allowed_names = {
                'abs': abs, 'round': round,
                'sqrt': math.sqrt, 'pow': pow,
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'log': math.log, 'exp': math.exp,
                'pi': math.pi, 'e': math.e
            }
            
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            return {
                "result": result,
                "expression": expression,
                "success": True
            }
        except Exception as e:
            return {
                "result": None,
                "expression": expression,
                "success": False,
                "error": str(e)
            }


if __name__ == "__main__":
    # Test MathSolver
    print("🧮 Testing MathSolver...")
    solver = MathSolver()
    
    test_problem = "Một quả bóng rơi từ độ cao h = 10m. Tính vận tốc khi chạm đất (g = 10 m/s²)"
    result = solver.solve(test_problem, problem_type="physics")
    print(f"Answer: {result['answer']}")
    print(f"Reasoning: {result['reasoning']}")
    
    # Test Calculator
    print("\n🔢 Testing Calculator...")
    calc = Calculator()
    calc_result = calc.calculate("2 + 2 * 3")
    print(f"Result: {calc_result}")
