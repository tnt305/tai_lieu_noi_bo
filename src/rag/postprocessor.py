"""
Postprocessor - Format output to {"qid": str, "answer": str}
"""
import re
from typing import Dict, Optional


class VNPTAI_PostProcessor:
    """
    Standardize LLM output to {"qid": str, "answer": str}
    """
    
    def format_output(self, raw_answer: str, qid: str = None, query: str = None) -> Dict[str, str]:
        """
        Format to standard output
        
        Args:
            raw_answer: LLM raw output
            qid: Question ID
            query: Original query (optional)
        
        Returns:
            {"qid": str, "answer": str}
        """
        # Extract clean answer
        answer = VNPTAI_PostProcessor._extract_answer(raw_answer)
        
        # Validate and clean
        answer = VNPTAI_PostProcessor._validate_format(answer)
        
        return {
            "qid": qid or "unknown",
            "answer": answer
        }
    
    @staticmethod
    def _extract_answer(text: str) -> str:
        """
        Extract final answer from LLM output
        
        Priority:
        1. "Câu trả lời thứ X" pattern
        2. JSON {"final_answer": "..."} or {"answer": "..."}
        3. Step 5/Conclude section
        4. Last meaningful line
        """
        if not text:
            return ""
        
        # Strategy 1: Multiple choice pattern - Extract letter only!
        mc_patterns = [
            r'câu trả lời(?: là)?:?\s*(?:thứ\s*)?([A-D]|\d)',
            r'đáp án(?: là)?:?\s*(?:thứ\s*)?([A-D]|\d)',
            r'chọn(?: đáp án)?:?\s*(?:thứ\s*)?([A-D]|\d)',
            r'\b([A-D])\.\s*(?:đúng|correct)',
            # Direct letter answer patterns
            r'["\']answer["\']\s*:\s*["\']([A-E])["\']',  # JSON {"answer": "C"}
            r'answer[:\s]+([A-E])\b',  # answer: C or answer C
        ]
        
        for pattern in mc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                answer_idx = match.group(1).upper()
                # Convert number to letter if needed (1->A, 2->B, etc.)
                if answer_idx.isdigit():
                    num = int(answer_idx)
                    if 1 <= num <= 5:
                        answer_idx = chr(64 + num)  # 1->A, 2->B...
                return answer_idx  # ✅ Return LETTER ONLY, not "Câu trả lời thứ X"
        
        # Strategy 2: JSON extraction
        json_patterns = [
            r'"final_answer"\s*:\s*"([^"]+)"',
            r'"answer"\s*:\s*"([^"]+)"',
            r'"đáp án"\s*:\s*"([^"]+)"',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Strategy 3: Step 5/Conclude section
        conclude_patterns = [
            r'(?:bước 5|step 5|kết luận|conclude)[:\s]*(.+?)(?:\n|$)',
            r'(?:đáp án cuối cùng|final answer)[:\s]*(.+?)(?:\n|$)',
        ]
        
        for pattern in conclude_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                answer = match.group(1).strip()
                if len(answer) < 200:  # Reasonable length
                    return answer
        
        # Strategy 4: Last meaningful line
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            # Skip lines that are just formatting
            for line in reversed(lines):
                if len(line) > 2 and not line.startswith('```'):
                    return line[:200]
        
        return text.strip()[:200]
    
    @staticmethod
    def _validate_format(answer: str) -> str:
        """Ensure answer meets requirements"""
        if not answer:
            return "Không có câu trả lời"
        
        # Truncate if too long
        if len(answer) > 500:
            answer = answer[:497] + "..."
        
        # Clean whitespace
        answer = ' '.join(answer.split())
        
        # Repair broken LaTeX
        answer = VNPTAI_PostProcessor._repair_latex(answer)

        return answer.strip()
    
    @staticmethod
    def _repair_latex(text: str) -> str:
        """
        Fix common LaTeX errors and control character corruptions.
        """
        # 1. Fix commonly broken commands (missing backslash or corrupted)
        # 1. Fix commonly broken commands
        # Replace 'rac{' that is NOT preceded by 'f'
        # Output DOUBLE backslash \\frac because user requires it (for JSON likely)
        text = re.sub(r'(?<!f)rac\{', r'\\\\frac{', text)
        
        # Also fix \rac{ -> \\frac{
        text = text.replace('\\rac{', '\\\\frac{')
        
        # 'sqrt' fixes: output \\sqrt
        text = text.replace(' sqrt', '\\\\sqrt').replace('sqrt{', '\\\\sqrt{')
        
        # 2. ENFORCE DOUBLE BACKSLASH for existing correct commands if strictly needed
        # User requested: "bắt buộc phải là \\frac"
        # We ensure single \frac becomes \\frac (but don't triple escape)
        text = re.sub(r'(?<!\\)\\frac', r'\\\\frac', text)
        text = re.sub(r'(?<!\\)\\sqrt', r'\\\\sqrt', text)
        
        # 3. Fix Greek letters and common symbols
        keywords = [
            'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa',
            'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 
            'phi', 'chi', 'psi', 'omega',
            'Delta', 'Gamma', 'Lambda', 'Omega', 'Phi', 'Pi', 'Psi', 'Sigma', 'Theta',
            'int', 'sum', 'infty', 'approx', 'leq', 'geq', 'pm', 'mp', 'sin', 'cos', 'tan', 'cot', 'log', 'ln'
        ]
        
        for kw in keywords:
            # Fix missing backslash: " beta " -> " \\beta " (Double backslash)
            text = text.replace(f' {kw} ', f' \\\\{kw} ')
            text = text.replace(f' {kw}{{', f' \\\\{kw}{{')
                                
            # If it has single backslash, ensure double if user wants strict \\kw?
            # Let's apply double backslash rule generically for keywords if they are latex
            text = re.sub(f'(?<!\\\\)\\\\{kw}\\b', f'\\\\\\\\{kw}', text)

        # 4. Handle specific control char corruptions
        text = text.replace('\x08eta', '\\\\beta')
        text = text.replace('\theta', '\\\\theta') 
        text = text.replace('\rho', '\\\\rho')

        # 5. FIX SPACING in Math Formulas: $ content $
        # Regex to find content between $...$ and pad with spaces
        # Note: avoid matching empty $$
        def pad_math(match):
            content = match.group(1).strip()
            if not content: return "$$"
            return f"$ {content} $"
            
        text = re.sub(r'\$([^$]+)\$', pad_math, text)

        return text
    
    @staticmethod
    def batch_format(results: list, qids: list) -> list:
        """Format multiple results"""
        processor = VNPTAI_PostProcessor()
        return [
            processor.format_output(result, qid)
            for result, qid in zip(results, qids)
        ]


if __name__ == "__main__":
    # Test postprocessor
    processor = VNPTAI_PostProcessor()
    
    test_cases = [
        ("Câu trả lời thứ 2", "q001"),
        ('{"final_answer": "10.25%", "reasoning": "..."}', "q002"),
        ("Bước 5: Kết luận\nĐáp án là 42", "q003"),
        ("Dựa trên phân tích:\n- A sai\n- B đúng\nĐáp án: B", "q004"),
    ]
    
    for raw, qid in test_cases:
        result = processor.format_output(raw, qid)
        print(f"QID: {result['qid']}, Answer: {result['answer']}")
