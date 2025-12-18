"""
PII (Personal Identifiable Information) Scanner
Hỗ trợ tiếng Việt: phát hiện CCCD, CMND, email, phone, etc.
"""
import re
import hashlib
from typing import Tuple, List, Dict, Pattern

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from rag.guardrails.base import Scanner

# Redaction modes
REDACT_PARTIAL = "partial"
REDACT_ALL = "all"
REDACT_HASH = "hash"


class VietnamesePIIPatterns:
    """Vietnamese PII regex patterns"""
    
    # CCCD (Căn cước công dân) - 12 số
    cccd = re.compile(r'\b\d{12}\b')
    
    # CMND (Chứng minh nhân dân) - 9 hoặc 12 số
    cmnd = re.compile(r'\b\d{9}\b')
    
    # Số điện thoại Việt Nam
    # Format: 0xxx-xxx-xxx, +84xxx-xxx-xxx, 84xxx-xxx-xxx
    phone = re.compile(r'(?:\+84|84|0)[0-9]{9,10}\b')
    
    # Email
    email = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    
    # Địa chỉ IP
    ip_address = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    
    # Số tài khoản ngân hàng (thường 6-16 số)
    bank_account = re.compile(r'\b\d{6,16}\b')
    
    # Mã số thuế (10-13 số)
    tax_code = re.compile(r'\b\d{10,13}\b')
    
    # Tên người (Vietnamese names - heuristic) - DISABLED
    # Common Vietnamese surnames
    # vietnamese_name = re.compile(
    #     r'\b(?:Nguyễn|Trần|Lê|Phạm|Hoàng|Huỳnh|Phan|Vũ|Võ|Đặng|Bùi|Đỗ|Hồ|Ngô|Dương|Lý)\s+'
    #     r'(?:[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+\s*){1,3}',
    #     re.UNICODE
    # )

    @classmethod
    def get_all_patterns(cls) -> Dict[str, Pattern]:
        """Get all PII patterns (excluding Vietnamese names)"""
        return {
            'cccd': cls.cccd,
            'cmnd': cls.cmnd,
            'phone': cls.phone,
            'email': cls.email,
            'ip_address': cls.ip_address,
            'bank_account': cls.bank_account,
            'tax_code': cls.tax_code,
            # 'vietnamese_name': cls.vietnamese_name,  # DISABLED - bỏ qua tên người
        }


class PIIScanner(Scanner):
    """
    PII Scanner - phát hiện thông tin cá nhân (Vietnamese support)
    
    Phát hiện:
    - CCCD, CMND
    - Số điện thoại Việt Nam
    - Email
    - IP address
    - Số tài khoản ngân hàng
    - Mã số thuế
    (Tên người đã bị disable)
    """
    
    def __init__(self, redact_mode: str = REDACT_ALL, entity_types: List[str] = None):
        """
        Khởi tạo PII scanner.
        
        Args:
            redact_mode: Chế độ ẩn
            entity_types: Danh sách loại PII cần detect (None = tất cả)
        """
        self._redact_mode = redact_mode
        
        # Get all patterns
        all_patterns = VietnamesePIIPatterns.get_all_patterns()
        
        # Filter by entity_types if specified
        if entity_types:
            self._patterns = {k: v for k, v in all_patterns.items() if k in entity_types}
        else:
            self._patterns = all_patterns
    
    @staticmethod
    def redact_value(value: str, mode: str) -> str:
        """Ẩn giá trị PII theo mode."""
        if mode == REDACT_PARTIAL:
            if len(value) <= 4:
                return "****"
            # Show first 2 and last 2 chars
            return f"{value[:2]}...{value[-2:]}"
        elif mode == REDACT_HASH:
            return hashlib.md5(value.encode()).hexdigest()[:8] + "..."
        elif mode == REDACT_ALL:
            return "[REDACTED]"
        else:
            raise ValueError(f"Unknown redact mode: {mode}")
    
    def scan(self, prompt: str) -> dict:
        """
        Quét và phát hiện PII trong prompt.
        
        Returns:
            dict với keys:
                - prediction: "Safe" hoặc "Has PII"
                - is_valid: True nếu không có PII, False nếu có
                - task: "pii" (task identifier)
        """
        if not prompt or prompt.strip() == "":
            return {
                "prediction": "Safe",
                "is_valid": True,
                "task": "pii"
            }
        
        found_pii: List[Tuple[str, str, int, int]] = []
        
        # Scan all PII patterns
        for pii_type, pattern in self._patterns.items():
            for match in pattern.finditer(prompt):
                pii_value = match.group(0)
                
                found_pii.append((
                    pii_type,
                    pii_value,
                    match.start(),
                    match.end()
                ))
        
        # No PII found
        if not found_pii:
            return {
                "prediction": "Safe",
                "is_valid": True,
                "task": "pii"
            }
        
        # Sort by position (reverse)
        found_pii.sort(key=lambda x: x[2], reverse=True)
        
        # Remove duplicates
        unique_pii = []
        seen_positions = set()
        for pii in found_pii:
            pos = (pii[2], pii[3])
            if pos not in seen_positions:
                unique_pii.append(pii)
                seen_positions.add(pos)
        
        # Collect PII types found
        pii_types_found = set()
        for pii_type, _, _, _ in unique_pii:
            pii_types_found.add(pii_type)
        
        print(f"⚠️  Detected {len(unique_pii)} PII(s): {', '.join(pii_types_found)}")
        
        return {
            "prediction": "Has PII",
            "is_valid": False,
            "task": "pii"
        }
