import re
import requests
import json
from typing import List, Dict, Optional, Any
from src.functional.common import clean_math_text, fuzzy_math_match
from src.functional.refusal import RefusalDetector
from src.guardrails.layer import ContentGuardrails
from src.rag.intention.router import IntentRouter
from src.etl.embedders import VNPTAIEmbedder
from src import load_llm_config
from src.functional.constants import API_URL

# Constants for Safety Checks
UNSAFE_KEYWORDS = ["chống phá", "tham nhũng", "lợi dụng", "phá hoại", "gây hại", "gây thương tích"]

class AnswerVerifier:
    """
    Encapsulates verification and refinement logic:
    1. Safety/Refusal Checks (Intent, Toxicity, Keywords)
    2. Answer Normalization (Regex)
    3. Ambiguity Resolution (Large LLM re-run if needed)
    4. Fallback Matching (Fuzzy, Embedding)
    """
    def __init__(self, 
                 router: Optional[IntentRouter] = None,
                 guardrails: Optional[ContentGuardrails] = None,
                 embedder: Optional[VNPTAIEmbedder] = None,
                 refusal_detector: Optional[RefusalDetector] = None):
        
        self.router = router
        self.guardrails = guardrails
        self.embedder = embedder or VNPTAIEmbedder()
        self.refusal_detector = refusal_detector or RefusalDetector(self.embedder)
        self.large_config = load_llm_config('large')
        self.api_url = API_URL

    def verify(self, query: str, choices: List[str], raw_answer: str, qid: str = "unknown") -> str:
        """
        Run full verification pipeline on the answer.
        Returns the finalized answer (typically a single letter A-E, or refusal text).
        """
        final_answer = raw_answer.strip()
        
        # --- 1. SAFETY & REFUSAL CHECK ---
        is_unsafe = self._check_safety(query)
        if is_unsafe:
            refusal_opt = self.refusal_detector.detect(choices)
            if refusal_opt:
                # print(f"   🛑 Forced Refusal (Safety): {refusal_opt}")
                return refusal_opt
            # If unsafe but no refusal option found, proceed (or strictly fail? Post-inf logic allowed proceed)
            
        # --- 2. FORMAT REFINEMENT ---
        # 2.1 Simple Regex "A", "A.", "A "
        match_simple = re.match(r'^([A-Z])\.?\s*$', final_answer, re.IGNORECASE)
        if match_simple:
            return match_simple.group(1).upper()

        # 2.2 Prefix "A. Content"
        match_prefix = re.match(r'^([A-Z])\.\s', final_answer, re.IGNORECASE)
        if match_prefix:
            return match_prefix.group(1).upper()
            
        # --- 3. AMBIGUITY RESOLUTION (LLM) ---
        # If we get here, the answer is messy.
        # print(f"   🔄 Resolving Ambiguous Answer for {qid}...")
        regenerated = self._solve_ambiguous_llm(query, choices, raw_answer)
        
        # Check regenerated
        match_regen = re.match(r'^([A-Z])\.?\s*$', regenerated, re.IGNORECASE)
        if match_regen:
            return match_regen.group(1).upper()
            
        # --- 4. FALLBACK MATCHING (Embedding/Fuzzy) ---
        # print(f"   ⚠️ Fallback Matching for {qid}...")
        target_text = regenerated if len(regenerated) > len(raw_answer) else raw_answer
        
        # 4.1 Fuzzy Math
        fuzzy_idx = fuzzy_math_match(target_text, choices)
        if fuzzy_idx != -1:
            return chr(65 + fuzzy_idx)
            
        # 4.2 Embedding Similarity
        return self._get_best_match_embedding(target_text, choices)

    def _check_safety(self, query: str) -> bool:
        """Check Intent, Keywords, and Toxicity"""
        # A. Intent
        if self.router:
            routing = self.router.route(query)
            category = routing.get('category', 'General')
            prob = routing.get('probs', {}).get('Refusal', 0.0)
            
            if category == 'Refusal': return True
            if prob > 0.1:
                q_lower = query.lower()
                if any(k in q_lower for k in UNSAFE_KEYWORDS): return True
        
        # B. Toxicity
        if self.guardrails and self.guardrails.toxicity_scanner:
            try:
                tox = self.guardrails.toxicity_scanner.scan(query)
                # Correct logic: check confidence score directly or use is_toxic
                # Original logic was tox_res.get('toxicity') > 0.5 (which was buggy fixed to confidence)
                # But scanner.scan returns 'is_toxic' boolean too.
                # Let's rely on confidence score to be consistent with previous fix
                score = tox.get('confidence', {}).get('Toxic/Harm', 0.0)
                if score > 0.4: return True
            except: pass
            
        return False

    def _solve_ambiguous_llm(self, query: str, choices: List[str], current_answer: str) -> str:
        """Call Large LLM to resolve ambiguity."""
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        sys_prompt = "Bạn là chuyên gia. Giải quyết tranh chấp hoặc lỗi, chọn 01 đáp án đúng duy nhất (A, B, C...)."
        user_msg = (
            f"Câu hỏi: {query}\nCác lựa chọn:\n{choices_str}\n\n"
            f"Câu trả lời cũ (gây nhiễu): {current_answer}\n\n"
            "Hãy chọn lại đáp án đúng nhất. Trả về JSON: {\"answer\": \"X\"}"
        )
        
        headers = {
            'Authorization': self.large_config.get('authorization', ''),
            'Token-id': self.large_config.get('tokenId', ''),
            'Token-key': self.large_config.get('tokenKey', ''),
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'vnptai_hackathon_large',
            'messages': [ {'role':'system', 'content': sys_prompt}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 512,
            'temperature': 0.5
        }
        
        try:
            resp = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                content = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
                # Extract JSON
                match = re.search(r'\{\s*["\']?answer["\']?\s*:\s*["\']?([^"\'}\\n]+)["\']?\s*\}', content, re.IGNORECASE)
                if match: return match.group(1).strip()
                # Extract Letter at end
                clean = content.replace("```json", "").replace("```", "").strip()
                match_l = re.search(r'\b([A-Z])\b\s*$', clean)
                if match_l: return match_l.group(1)
                return content
        except: pass
        return current_answer

    def _get_best_match_embedding(self, answer_text: str, choices: List[str]) -> str:
        """Match answer text to choices using embedding cosine similarity."""
        if not choices: return "A"
        try:
            # Embed all: [answer, choice1, choice2...]
            valid_choices = [c for c in choices if c.strip()]
            if not valid_choices: return "A"
            
            texts = [answer_text] + valid_choices
            embeddings = self.embedder.embed(texts)
            
            if not embeddings or len(embeddings) < 2: return "A"
            
            ans_vec = embeddings[0]
            choice_vecs = embeddings[1:]
            
            # Manual Cosine Sim (avoid depending on sklearn/scipy if not needed, similar to post_inference logic)
            def cosine(v1, v2):
                dot = sum(a*b for a,b in zip(v1, v2))
                mag1 = sum(a*a for a in v1) ** 0.5
                mag2 = sum(b*b for b in v2) ** 0.5
                if mag1 == 0 or mag2 == 0: return 0
                return dot / (mag1 * mag2)

            best_idx = 0
            best_score = -1
            
            for i, vec in enumerate(choice_vecs):
                score = cosine(ans_vec, vec)
                if score > best_score:
                    best_score = score
                    best_idx = i
            
            return chr(65 + best_idx)
        except:
             return "A"
