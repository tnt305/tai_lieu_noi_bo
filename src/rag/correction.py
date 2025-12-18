"""
Smart CorrectionBank: Learn from validation mistakes to improve future inference.

Key Features:
- Stores "Reasoning Rules" extracted from wrong predictions.
- Smart Dispatch: Uses Small LLM for General, Large LLM for Math/RAG.
- Quota Banking: Holds saved quota for immediate use on next error.
- Persistent: Saves rules to disk for reuse.
"""

import os
import pickle
import json
import requests
try:
    import numpy as np
except ImportError:
    np = None
    print("⚠️ numpy not found. CorrectionBank running in no-vector mode.")
from typing import Dict, List, Optional
from collections import deque
import time

from src import load_llm_config


class QuotaExhaustedException(Exception):
    """Raised when LLM quota is exhausted. Script should stop and resume after 1 hour."""
    def __init__(self, model_type: str, wait_minutes: float):
        self.model_type = model_type
        self.wait_minutes = wait_minutes
        super().__init__(f"{model_type} LLM quota exhausted. Please wait {wait_minutes:.1f} minutes and re-run.")


# API Endpoints (same as inference.py)
from src.functional.constants import API_URL as API_URL_LARGE, API_URL_SMALL


class CorrectionBank:
    """
    Stores and retrieves "Reasoning Rules" based on past errors.
    
    Rules are indexed by query embedding for semantic retrieval.
    """
    
    def __init__(
        self, 
        rules_file: str = "dataset/correction_rules.pkl",
        threshold: float = 0.75,  # Lower threshold than cache to catch more patterns
        auto_save: bool = True
    ):
        self.rules_file = rules_file
        self.threshold = threshold
        self.auto_save = auto_save
        
        # Storage
        self.vectors: List[np.ndarray] = []
        self.rules: List[Dict] = []  # {query, rule, intent, context_hash}
        
        # Quota Banking: Number of "held" Large LLM calls (to use immediately)
        self.held_large_quota = 0
        
        # Rate Limiters for Reflexion calls
        self.small_limiter = RateLimiter(max_calls_per_hour=55)
        self.large_limiter = RateLimiter(max_calls_per_hour=35)
        
        # LLM Configs
        self.small_config = load_llm_config('small')
        self.large_config = load_llm_config('large')
        
        self._unsaved_changes = 0
        self.load()
    
    def save(self):
        """Save rules to JSONL (for Qdrant) and vectors to pickle (for cache)"""
        try:
            # Save rules as JSONL (one JSON object per line)
            jsonl_file = self.rules_file.replace('.pkl', '.jsonl')
            with open(jsonl_file, 'w', encoding='utf-8') as f:
                for i, rule in enumerate(self.rules):
                    # Create Qdrant-ready document
                    doc = {
                        'id': f"rule_{i}",
                        'query': rule['query'],
                        'correction_tip': rule['correction_tip'],
                        'reasoning': {
                            'wrong_answer_text': rule['wrong_answer'],  # Full LLM output (reasoning)
                            'correct_answer': rule['correct_answer']
                        },
                        'metadata': {
                            'intent': rule['intent'],
                            'context_hash': rule.get('context_hash'),
                            'source': 'validation_learning',
                            'timestamp': rule.get('timestamp', '')
                        }
                    }
                    f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            
            # Save vectors + held_quota as pickle (for fast loading)
            vector_cache = {
                'vectors': self.vectors,
                'held_large_quota': self.held_large_quota
            }
            with open(self.rules_file, 'wb') as f:
                pickle.dump(vector_cache, f)
            
            print(f"💾 CorrectionBank saved:")
            print(f"   - Rules (JSONL): {jsonl_file} ({len(self.rules)} rules)")
            print(f"   - Vectors (PKL): {self.rules_file}")
            self._unsaved_changes = 0
        except Exception as e:
            print(f"⚠️ Failed to save CorrectionBank: {e}")
    
    def load(self):
        """Load rules from JSONL and vectors from pickle"""
        jsonl_file = self.rules_file.replace('.pkl', '.jsonl')
        
        # Load vectors + quota from pickle
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'rb') as f:
                    data = pickle.load(f)
                self.vectors = data.get('vectors', [])
                self.held_large_quota = data.get('held_large_quota', 0)
            except Exception as e:
                print(f"⚠️ Failed to load vectors: {e}")
        
        # Load rules from JSONL
        if os.path.exists(jsonl_file):
            try:
                self.rules = []
                with open(jsonl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        doc = json.loads(line.strip())
                        # Reconstruct rule from JSONL doc
                        rule = {
                            'query': doc['query'],
                            'correction_tip': doc['correction_tip'],
                            'intent': doc['metadata']['intent'],
                            'context_hash': doc['metadata'].get('context_hash'),
                            'wrong_answer': doc.get('reasoning', {}).get('wrong_answer_text', 
                                                    doc.get('metadata', {}).get('wrong_answer', '')),
                            'correct_answer': doc.get('reasoning', {}).get('correct_answer',
                                                     doc.get('metadata', {}).get('correct_answer', ''))
                        }
                        self.rules.append(rule)
                print(f"📂 Loaded CorrectionBank:")
                print(f"   - {len(self.rules)} rules from {jsonl_file}")
                print(f"   - {len(self.vectors)} vectors, {self.held_large_quota} held quota")
            except Exception as e:
                print(f"⚠️ Failed to load rules: {e}")
    
    def add_hold(self):
        """
        Bank saved quota when a prediction is correct.
        Will be used immediately for the next error case.
        """
        self.held_large_quota += 1
        print(f"🏦 Quota Banked! Total held: {self.held_large_quota}")
        if self.auto_save:
            self.save()
    
    def lookup(self, query_vector: List[float], context_hash: str = None) -> Optional[str]:
        """
        Find applicable correction rules for similar past errors.
        Returns the rule text if found, None otherwise.
        """
        if not self.vectors or np is None:
            if np is None:
                # Fallback: maybe exact match if we had it, but for now just pass
                pass
            return None
        
        try:
            # Filter by context_hash if provided (strict mode)
            # For more lenient matching (just question similarity), set context_hash=None
            valid_indices = []
            for i, rule in enumerate(self.rules):
                if context_hash is None or rule.get('context_hash') == context_hash:
                    valid_indices.append(i)
            
            if not valid_indices:
                # Fallback: search all rules if no context match
                valid_indices = list(range(len(self.rules)))
            
            subset_vectors = [self.vectors[i] for i in valid_indices]
            
            query_vec = np.array(query_vector)
            cache_matrix = np.stack(subset_vectors)
            
            query_norm = np.linalg.norm(query_vec)
            cache_norms = np.linalg.norm(cache_matrix, axis=1)
            dot_products = np.dot(cache_matrix, query_vec)
            similarities = dot_products / (cache_norms * query_norm + 1e-9)
            
            best_rel_idx = np.argmax(similarities)
            best_score = similarities[best_rel_idx]
            original_idx = valid_indices[best_rel_idx]
            
            if best_score >= self.threshold:
                rule = self.rules[original_idx]
                print(f"📖 Found Correction Rule (Sim: {best_score:.3f})")
                return rule['correction_tip']
        
        except Exception as e:
            print(f"⚠️ CorrectionBank lookup error: {e}")
        
        return None
    
    def add_error(
        self,
        query: str,
        query_vector: List[float],
        wrong_answer: str,
        correct_answer: str,
        intent: str,  # From IntentRouter: 'general', 'math', 'rag', etc.
        context_hash: str = None,
        context_snippet: str = None
    ):
        """
        Process an error case: Generate and store a correction rule.
        
        Strategy: 
        - Small LLM is used for initial inference (in distil.py)
        - Large LLM is ALWAYS used here for Reflexion (error correction)
        - This optimizes quota: Small for fast inference, Large for accurate correction
        """
        # Always use Large LLM for Reflexion/error correction
        # Small LLM was already used for inference, now Large corrects the error
        use_large = True
        
        print(f"🔧 Reflexion: Using Large LLM to analyze error and generate correction rule")
        
        # Generate correction rule
        correction_tip = self._generate_rule(
            query=query,
            wrong_answer=wrong_answer,
            correct_answer=correct_answer,
            context_snippet=context_snippet,
            use_large=use_large
        )
        
        if correction_tip:
            if np is not None:
                self.vectors.append(np.array(query_vector))
            else:
                 # Should probably keep indices aligned, so append list or None
                 self.vectors.append(query_vector) # Just append raw list if no numpy
                 
            self.rules.append({
                'query': query,
                'correction_tip': correction_tip,
                'intent': intent,
                'context_hash': context_hash,
                'wrong_answer': wrong_answer,
                'correct_answer': correct_answer
            })
            
            self._unsaved_changes += 1
            if self.auto_save and self._unsaved_changes >= 3:
                self.save()
            
            print(f"✅ Added Correction Rule: {correction_tip[:100]}...")
    
    def _generate_rule(
        self,
        query: str,
        wrong_answer: str,
        correct_answer: str,
        context_snippet: str = None,
        use_large: bool = True
    ) -> Optional[str]:
        """
        Call LLM to analyze the error and generate a general correction rule.
        Raises QuotaExhaustedException if quota is exhausted (instead of sleeping).
        """
        # Check quota and RAISE exception if exhausted (don't sleep)
        if use_large:
            wait_time = self.large_limiter.check_quota()
            if wait_time > 0:
                raise QuotaExhaustedException("Large", wait_time / 60)
            self.large_limiter.record_call()
            api_url = API_URL_LARGE
            config = self.large_config
            model_name = 'vnptai_hackathon_large'
        else:
            wait_time = self.small_limiter.check_quota()
            if wait_time > 0:
                raise QuotaExhaustedException("Small", wait_time / 60)
            self.small_limiter.record_call()
            api_url = API_URL_SMALL
            config = self.small_config
            model_name = 'vnptai_hackathon_small'
        
        # Build Reflexion Prompt
        system_prompt = """Bạn là chuyên gia phân tích lỗi suy luận AI.
Nhiệm vụ: Phân tích TẠI SAO model trả lời sai và tạo MẸO SỬA LỖI ngắn gọn.
Mẹo phải TỔNG QUÁT (áp dụng được cho các câu tương tự), không nhắc lại đáp án cụ thể.
Chỉ trả lời MẸO SỬA LỖI, không giải thích dài dòng."""

        context_part = ""
        if context_snippet:
            context_part = f"\n\nNgữ cảnh (tóm tắt): {context_snippet[:500]}..."
        
        user_prompt = f"""Câu hỏi: {query}{context_part}

Model trả lời SAI: {wrong_answer}
Đáp án ĐÚNG: {correct_answer}

Hãy phân tích lỗi và tạo MẸO SỬA LỖI tổng quát (1-2 câu):"""

        headers = {
            'Authorization': config.get('authorization', ''),
            'Token-id': config.get('tokenId', ''),
            'Token-key': config.get('tokenKey', ''),
            'Content-Type': 'application/json'
        }
        
        json_data = {
            'model': model_name,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.5,
            'max_completion_tokens': 256
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=json_data, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # Record successful call
            if use_large:
                self.large_limiter.record_call()
            else:
                self.small_limiter.record_call()
                
            return content.strip() if content else None
            
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                print(f"\n🚨 401 Unauthorized (Quota/Auth) in CorrectionBank")
                raise QuotaExhaustedException("Large" if use_large else "Small", 60.0)
            print(f"⚠️ Reflexion LLM error: {e}")
            return None
            
        except Exception as e:
            print(f"⚠️ Reflexion LLM error: {e}")
            return None


class RateLimiter:
    """
    Sliding window rate limiter.
    Now supports check_quota() + record_call() pattern for non-blocking quota check.
    """
    def __init__(self, max_calls_per_hour: int):
        self.max_calls = max_calls_per_hour
        self.timestamps = deque()
    
    def _cleanup_old(self):
        """Remove timestamps older than 1 hour"""
        now = time.time()
        while self.timestamps and now - self.timestamps[0] > 3600:
            self.timestamps.popleft()
    
    def check_quota(self) -> float:
        """
        Check if quota is available.
        Returns: 0 if quota available, otherwise wait time in seconds until quota resets.
        """
        self._cleanup_old()
        
        if len(self.timestamps) >= self.max_calls:
            oldest = self.timestamps[0]
            now = time.time()
            wait_time = 3600 - (now - oldest) + 5  # +5s buffer
            return max(0, wait_time)
        
        return 0
    
    def record_call(self):
        """Record a successful API call timestamp"""
        self._cleanup_old()
        self.timestamps.append(time.time())
    
    def wait_if_needed(self):
        """Sleep if rate limit reached (legacy method)"""
        wait_time = self.check_quota()
        if wait_time > 0:
            print(f"\n⏳ CorrectionBank Rate Limit ({self.max_calls}/h). Waiting {wait_time/60:.1f} min...")
            time.sleep(wait_time)
            return self.wait_if_needed()
        
        self.record_call()

