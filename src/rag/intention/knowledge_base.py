"""
Knowledge Base for VNPTAI Intent Classifier
Given a user query, split it into knowledge part and question main function for RAG contextual handle
using Rule-based
"""

from abc import abstractmethod
import re
from typing import Tuple
from rank_bm25 import BM25Plus
from underthesea import sent_tokenize, word_tokenize

from src.rag.intention.base import Extractor

class KnowledgeBase(Extractor):
    def __init__(self, query: str):
        self.query = query

    def clean_text(self, text):
        # Thay \n\n hoặc \n bằng dấu hai chấm
        text = re.sub(r'\n\s*\n', ' : ', text)
        text = re.sub(r'\n', ' : ', text)
        return text.strip()

    def extractive_bm25(self, question, text, top_k=3):
        # Làm sạch trước (tùy bạn, có thể làm sau)
        text = self.clean_text(text)

        # 1) Tách câu
        sentences = sent_tokenize(text)

        # 2) Tokenize tiếng Việt
        tokenized = [word_tokenize(s.lower()) for s in sentences]

        # 3) BM25Plus tối ưu cho QA
        bm25 = BM25Plus(tokenized, k1=1.0, b=0.3)

        # 4) Tính điểm
        q_tokens = word_tokenize(question.lower())
        scores = bm25.get_scores(q_tokens)

        # 5) Lấy top-k
        idx = scores.argsort()[::-1][:top_k]
        selected = [sentences[i] for i in idx]

        # 6) Gom thành 1 đoạn
        combined = " ".join(selected)

        return combined 

    def extract(self, query: str) -> Tuple[str, str]:
        
        knowledge = self.extractive_bm25(query, self.query)
        query= query.strip()
        return knowledge, query


class VNPTAI_KNOWLEDGE_BASE(KnowledgeBase):
    def __init__(self, query: str):
        super().__init__(query)


    def extractive_bm25(self, question, text, top_k=10):
        return super().extractive_bm25(question, text, top_k)

