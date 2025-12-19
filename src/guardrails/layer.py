"""
Guardrails Layer - Content Safety Check
Runs BEFORE classification/routing

Flow: Query -> Guardrails -> VNPT Classifier -> IntentRouter -> ...

Checks:
1. Toxicity (content_safety)
2. PII (privacy/pii)
3. Secrets (privacy/secrets)

If violation detected AND refusal choice exists -> return refusal immediately
Otherwise -> continue normal flow
"""
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class GuardrailResult:
    """Result from guardrails check"""
    is_safe: bool
    violations: List[str]  # List of violation types
    should_refuse: bool  # True if should return refusal answer
    refusal_answer: Optional[str]  # The refusal choice if found
    refusal_index: Optional[int]  # 1-based index of refusal choice


class ContentGuardrails:
    """
    Content safety guardrails layer
    Checks toxicity, PII, and secrets before processing
    """
    
    # Patterns for refusal-like choices
    REFUSAL_PATTERNS = [
        r'tôi không thể cung cấp',
        r'không thể cung cấp thông tin',
        r'thông tin này không được',
        r'thông tin này chưa được',
        r'chưa được xác minh',
        r'không được xác minh',
        r'không có thông tin',
        r'không thể trả lời',
        r'không được phép',
        r'vi phạm chính sách',
        r'không hỗ trợ',
        r'từ chối cung cấp',
        r'không xác định được',
        r'chưa xác định được',
    ]
    
    def __init__(
        self,
        enable_toxicity: bool = True,
        enable_pii: bool = True,
        enable_secrets: bool = True,
        toxicity_model_path: str = "./models/guardrails/toxicity"
    ):
        """
        Initialize guardrails
        
        Args:
            enable_toxicity: Check for toxic content
            enable_pii: Check for Vietnamese PII
            enable_secrets: Check for private keys/secrets
            toxicity_model_path: Path to toxicity ONNX model
        """
        self.enable_toxicity = enable_toxicity
        self.enable_pii = enable_pii
        self.enable_secrets = enable_secrets
        
        # Lazy load scanners
        self._toxicity_scanner = None
        self._pii_scanner = None
        self._secrets_scanner = None
        self._toxicity_model_path = toxicity_model_path
    
    @property
    def toxicity_scanner(self):
        """Lazy load ToxicityScanner"""
        if self._toxicity_scanner is None and self.enable_toxicity:
            try:
                from src.guardrails.content_safety.toxicity import ToxicityScanner
                self._toxicity_scanner = ToxicityScanner(
                    model_path=self._toxicity_model_path
                )
            except Exception as e:
                print(f"[WARN] ToxicityScanner not loaded: {e}")
        return self._toxicity_scanner
    
    @property
    def pii_scanner(self):
        """Lazy load PIIScanner"""
        if self._pii_scanner is None and self.enable_pii:
            try:
                from src.guardrails.privacy.pii import PIIScanner
                self._pii_scanner = PIIScanner()
            except Exception as e:
                print(f"[WARN] PIIScanner not loaded: {e}")
        return self._pii_scanner
    
    @property
    def secrets_scanner(self):
        """Lazy load PrivateKeyScanner"""
        if self._secrets_scanner is None and self.enable_secrets:
            try:
                from src.guardrails.privacy.secrets import PrivateKeyScanner
                self._secrets_scanner = PrivateKeyScanner()
            except Exception as e:
                print(f"[WARN] PrivateKeyScanner not loaded: {e}")
        return self._secrets_scanner
    
    def check(
        self,
        query: str,
        choices: Optional[List[str]] = None
    ) -> GuardrailResult:
        """
        Run all guardrail checks on query
        
        Args:
            query: User query
            choices: List of answer choices (if multiple choice question)
        
        Returns:
            GuardrailResult with safety status and potential refusal
        """
        violations = []
        
        # 1. Check toxicity
        if self.toxicity_scanner:
            toxicity_result = self.toxicity_scanner.scan(query)
            if toxicity_result.get('is_toxic', False):
                violations.append('toxicity')
                print(f"[WARN] Toxicity detected: {toxicity_result.get('prediction')}")
        
        # 2. Check PII
        if self.pii_scanner:
            pii_result = self.pii_scanner.scan(query)
            if not pii_result.get('is_valid', True):
                violations.append('pii')
                print(f"[WARN] PII detected: {pii_result.get('prediction')}")
        
        # 3. Check secrets
        if self.secrets_scanner:
            secrets_result = self.secrets_scanner.scan(query)
            if not secrets_result.get('is_valid', True):
                violations.append('secrets')
                print(f"[WARN] Secrets detected: {secrets_result.get('prediction')}")
        
        # If no violations, safe to proceed
        if not violations:
            return GuardrailResult(
                is_safe=True,
                violations=[],
                should_refuse=False,
                refusal_answer=None,
                refusal_index=None
            )
        
        # Violations found - check if refusal choice exists
        if choices:
            refusal_choice, refusal_idx = self._find_refusal_choice(choices)
            if refusal_choice:
                return GuardrailResult(
                    is_safe=False,
                    violations=violations,
                    should_refuse=True,
                    refusal_answer=refusal_choice,
                    refusal_index=refusal_idx
                )
        
        # Violations but no refusal choice - continue normal flow
        return GuardrailResult(
            is_safe=False,
            violations=violations,
            should_refuse=False,
            refusal_answer=None,
            refusal_index=None
        )
    
    def _find_refusal_choice(
        self,
        choices: List[str]
    ) -> Tuple[Optional[str], Optional[int]]:
        """
        Find refusal-like choice in answer options
        
        Args:
            choices: List of answer choices
        
        Returns:
            (refusal_choice, 1-based index) or (None, None)
        """
        for i, choice in enumerate(choices, 1):
            choice_lower = choice.lower()
            for pattern in self.REFUSAL_PATTERNS:
                if re.search(pattern, choice_lower):
                    return choice, i
        
        return None, None
    
    def format_refusal_answer(
        self,
        refusal_index: int,
        qid: str = None
    ) -> Dict[str, str]:
        """
        Format refusal answer to standard output
        
        Args:
            refusal_index: 1-based index of refusal choice
            qid: Question ID
        
        Returns:
            {"qid": str, "answer": str}
        """
        # Convert to A/B/C/D format if index <= 4
        if refusal_index <= 4:
            answer_letter = chr(64 + refusal_index)  # 1->A, 2->B, etc.
            answer = f"Câu trả lời thứ {answer_letter}"
        else:
            answer = f"Câu trả lời thứ {refusal_index}"
        
        return {
            "qid": qid or "unknown",
            "answer": answer
        }


class GuardrailsLayer:
    """
    High-level guardrails interface for orchestrator integration
    """
    
    def __init__(self, **kwargs):
        self.guardrails = ContentGuardrails(**kwargs)
    
    def process(
        self,
        query: str,
        choices: Optional[List[str]] = None,
        qid: str = None
    ) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Process query through guardrails
        
        Args:
            query: User query
            choices: Answer choices (optional)
            qid: Question ID
        
        Returns:
            (should_continue, result_if_refused)
            - (True, None) if should continue normal flow
            - (False, {"qid": ..., "answer": ...}) if should return refusal
        """
        result = self.guardrails.check(query, choices)
        
        if result.should_refuse and result.refusal_index:
            # Return refusal answer immediately
            answer = self.guardrails.format_refusal_answer(
                result.refusal_index,
                qid
            )
            print(f"Guardrails triggered: {result.violations}")
            print(f"   Returning refusal answer: {answer}")
            return False, answer
        
        if not result.is_safe:
            print(f"[WARN] Guardrails warning: {result.violations} (no refusal choice, continuing)")
        
        # Continue normal flow
        return True, None


# if __name__ == "__main__":
    # Test guardrails
    # print("=" * 60)
    # print("Testing Guardrails Layer")
    # print("=" * 60)
    
    # # Test without scanners (just pattern matching)
    # guardrails = ContentGuardrails(
    #     enable_toxicity=False,  # Disable for standalone test
    #     enable_pii=False,
    #     enable_secrets=False
    # )
    
    # # Test refusal pattern matching
    # test_choices = [
    #     "Đáp án là 42",
    #     "Tôi không thể cung cấp thông tin này",
    #     "Kết quả là 3.14",
    #     "Không có đáp án đúng"
    # ]
    
    # refusal, idx = guardrails._find_refusal_choice(test_choices)
    # print(f"\nTest choices: {test_choices}")
    # print(f" Found refusal choice at index {idx}: '{refusal}'")
    
    # # Test format
    # result = guardrails.format_refusal_answer(idx, "test_001")
    # print(f" Formatted result: {result}")
    
    # # More test patterns
    # more_choices = [
    #     ["Có thể", "Không thể", "Thông tin này chưa được xác minh", "Tất cả đều sai"],
    #     ["A", "B", "C", "D"],
    #     ["Không xác định được câu trả lời", "100", "200", "300"],
    # ]
    
    # print("\nMore refusal pattern tests:")
    # for choices in more_choices:
    #     refusal, idx = guardrails._find_refusal_choice(choices)
    #     if refusal:
    #         print(f"Found: '{refusal}' at index {idx}")
    #     else:
    #         print(f"No refusal in: {choices}")
