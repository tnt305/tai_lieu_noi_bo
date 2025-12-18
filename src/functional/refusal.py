import numpy as np
from typing import List, Optional

class RefusalDetector:
    def __init__(self, embedder):
        self.embedder = embedder
        # Keyword list for fast detection
        self.keywords = ["không thể trả lời", "tôi không thể", "không có thông tin", "từ chối"]
        
        # Anchor sentence for semantic comparison
        self.anchor_text = "Tôi không thể trả lời câu hỏi này"
        self._anchor_embedding = None

    def _get_anchor_embedding(self):
        """Lazy load anchor embedding to avoid API call on init"""
        if self._anchor_embedding is None:
            # Get embedding for the single anchor text
            start_time = 0
            # Ensure embedder has embed method
            if hasattr(self.embedder, 'embed'):
                 embeddings = self.embedder.embed([self.anchor_text])
                 if embeddings:
                     self._anchor_embedding = np.array(embeddings[0])
        return self._anchor_embedding

    def detect(self, choices: List[str]) -> Optional[str]:
        """
        Identify which choice is a Refusal answer.
        Strategy:
        1. Exact keyword match (fast & precise)
        2. Semantic similarity with anchor text (fallback)
        """
        if not choices:
            return None

        # 1. Keyword Search
        for i, c in enumerate(choices):
            c_lower = str(c).lower()
            if any(k in c_lower for k in self.keywords):
                return chr(65+i) # Return 'A', 'B', 'C', etc.
        
        # 2. Semantic Search (fallback)
        try:
            anchor_emb = self._get_anchor_embedding()
            if anchor_emb is None:
                return None
                
            # Embed all choices
            # Note: This makes an API call. Only used if keywords fail.
            choice_embs_list = self.embedder.embed(choices)
            if not choice_embs_list:
                return None
                
            choice_embs = np.array(choice_embs_list)
            
            # Cosine Similarity Calculation
            # sim(A, B) = (A . B) / (|A| * |B|)
            norm_anchor = np.linalg.norm(anchor_emb)
            norm_choices = np.linalg.norm(choice_embs, axis=1)
            
            # Avoid division by zero
            if norm_anchor == 0: return None
            # Handle zero vectors in choices
            valid_mask = norm_choices > 0
            if not np.any(valid_mask): return None
            
            similarities = np.zeros(len(choices))
            
            # Calculate similarity only for valid vectors
            similarities[valid_mask] = np.dot(choice_embs[valid_mask], anchor_emb) / (norm_choices[valid_mask] * norm_anchor)
            
            # Find index of max similarity
            best_idx = np.argmax(similarities)
            
            # Safety Threshold
            if similarities[best_idx] < 0.4:
                # print(f"   ⚠️ Refusal Detection: Max similarity {similarities[best_idx]:.2f} < 0.4. Ignoring.")
                return None
                
            return chr(65 + int(best_idx))
            
        except Exception as e:
            print(f"⚠️ Refusal Detection Error: {e}")
            return None
