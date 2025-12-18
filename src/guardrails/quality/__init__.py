"""
Quality Control Guardrails

Modules:
- language: Language detection (Vietnamese only)
- relevance: Context relevance for RAG
"""

from .language import LanguageScanner

__all__ = [
    'LanguageScanner',
]
