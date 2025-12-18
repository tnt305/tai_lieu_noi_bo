"""
Secrets Scanner - phát hiện và ẩn thông tin nhạy cảm

Sử dụng class attributes pattern - dễ đọc:
- SecretPatterns.openai
- SecretPatterns.github  
- SecretPatterns.slack
"""
import hashlib
from typing import Tuple, List

from ..base import Scanner
from .secret_patterns import SecretPatterns

# Redaction modes
REDACT_PARTIAL = "partial"
REDACT_ALL = "all"
REDACT_HASH = "hash"


class PrivateKeyScanner(Scanner):
    """
    Scanner để phát hiện secrets sử dụng Registry Pattern.
    
    Patterns được load từ ALL_SECRET_PATTERNS registry:
    - 65+ secret types
    - 93 pre-compiled regex patterns
    - API Keys, JWT Tokens, OAuth Tokens, Webhooks, etc.
    """
    
    def __init__(self, redact_mode: str = REDACT_ALL):
        """
        Khởi tạo scanner.
        
        Args:
            redact_mode: Chế độ ẩn secrets
                - REDACT_PARTIAL: Hiển thị 2 ký tự đầu/cuối
                - REDACT_ALL: Thay toàn bộ bằng ******
                - REDACT_HASH: Thay bằng MD5 hash
        """
        self._redact_mode = redact_mode
        # Use class attributes pattern - clean and readable
        self._patterns = SecretPatterns.get_all_patterns()
    
    @staticmethod
    def redact_value(value: str, mode: str) -> str:
        """Ẩn giá trị secret theo mode được chọn."""
        if mode == REDACT_PARTIAL:
            if len(value) <= 4:
                return "****"
            return f"{value[:2]}...{value[-2:]}"
        elif mode == REDACT_HASH:
            return hashlib.md5(value.encode()).hexdigest()
        elif mode == REDACT_ALL:
            return "******"
        else:
            raise ValueError(f"Unknown redact mode: {mode}")
    
    def scan(self, prompt: str) -> dict:
        """
        Quét và phát hiện secrets trong prompt.
        
        Args:
            prompt: Text cần quét
            
        Returns:
            dict với keys:
                - prediction: "Safe" hoặc "Has private key"
                - is_valid: True nếu không có secret, False nếu có
        """
        if not prompt or prompt.strip() == "":
            return {
                "prediction": "Safe",
                "is_valid": True
            }
        
        found_secrets: List[Tuple[str, str, int, int]] = []
        
        # Scan all patterns from registry
        for secret_type, patterns in self._patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(prompt):
                    # Get matched text
                    secret_value = match.group(0)
                    # If pattern has groups, use first group
                    if match.groups():
                        secret_value = match.group(1)
                    
                    found_secrets.append((
                        secret_type,
                        secret_value,
                        match.start(),
                        match.end()
                    ))
        
        # No secrets found
        if not found_secrets:
            return {
                "prediction": "Safe",
                "is_valid": True,
                "task": "private_key"
            }
        
        # Sort by position (reverse to not affect indices)
        found_secrets.sort(key=lambda x: x[2], reverse=True)
        
        # Remove duplicates (same position)
        unique_secrets = []
        seen_positions = set()
        for secret in found_secrets:
            pos = (secret[2], secret[3])
            if pos not in seen_positions:
                unique_secrets.append(secret)
                seen_positions.add(pos)
        
        # Collect secret types found
        secret_types_found = set()
        for secret_type, _, _, _ in unique_secrets:
            secret_types_found.add(secret_type)
        
        print(f"⚠️  Detected {len(unique_secrets)} secret(s): {', '.join(secret_types_found)}")
        
        return {
            "prediction": "Has private key",
            "is_valid": False,
            "task": "private_key"
        }