import math
from typing import List, Dict, Optional, Any
import json
import os
import pickle
import re

class SemanticQACache:
    """
    In-memory semantic cache for QA results.
    Uses vector similarity to find 'similar' questions.
    (Native Python Version - No Numpy)
    """
    
    def __init__(self, threshold: float = 0.90, cache_file: str = "semantic_cache.pkl", auto_save: bool = True): 
        self.threshold = threshold
        self.vectors = []  # List[List[float]]
        self.entries = []  # List[Dict] -> {'answer': str, 'qid': str, 'original_query': str}
        self.cache_file = cache_file
        self.auto_save = auto_save
        self._unsaved_changes = 0
        self.load() # Load existing cache on init

    def save(self):
        """Save cache to disk using pickle"""
        try:
            # Clean vectors to be pure lists just in case
            clean_vectors = [v if isinstance(v, list) else v.tolist() for v in self.vectors]
            
            data = {
                'vectors': clean_vectors,
                'entries': self.entries
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(data, f)
            print(f"## Cache saved to {self.cache_file} ({len(self.entries)} entries)")
            self._unsaved_changes = 0
        except Exception as e:
            print(f"## Failed to save cache: {e}")

    def load(self):
        """Load cache from disk"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self.vectors = data.get('vectors', [])
                    self.entries = data.get('entries', [])
                
                # Ensure vectors are lists (if loaded from legacy numpy save)
                if self.vectors and not isinstance(self.vectors[0], list):
                    self.vectors = [v.tolist() for v in self.vectors]
                    
                print(f"## Loaded cache from {self.cache_file} ({len(self.entries)} entries)")
            except Exception as e:
                print(f"## Failed to load cache: {e}")

    def lookup(self, query_vector: List[float], current_query: str, context_hash: str = None) -> Optional[Dict]:
        """
        Find similar query in cache with Number Sensitivity Check & Context Awareness
        """
        if not self.vectors:
            return None
            
        try:
            # Filter indices with matching context_hash
            valid_indices = []
            for i, entry in enumerate(self.entries):
                if entry.get('context_hash') == context_hash:
                    valid_indices.append(i)
            
            if not valid_indices:
                return None

            best_score = -1.0
            best_idx = -1
            
            # Precompute query norm
            q_norm = math.sqrt(sum(x*x for x in query_vector))
            
            for idx in valid_indices:
                cache_vec = self.vectors[idx]
                
                # Cosine Similarity
                dot_product = sum(a*b for a, b in zip(query_vector, cache_vec))
                c_norm = math.sqrt(sum(x*x for x in cache_vec))
                
                sim = dot_product / ((q_norm * c_norm) + 1e-9)
                
                if sim > best_score:
                    best_score = sim
                    best_idx = idx
            
            if best_score >= self.threshold and best_idx != -1:
                entry = self.entries[best_idx]
                cached_query = entry['original_query']
                
                # Number Sensitivity Check
                has_numbers = bool(re.search(r'\d', current_query))
                
                if has_numbers:
                    if current_query.strip().lower() != cached_query.strip().lower():
                        # print(f"## Cache Miss (Math Mismatch): '{current_query}' vs '{cached_query}'")
                        return None
                
                print(f"## Cache Hit! Sim: {best_score:.3f}")
                return entry['result']
                
        except Exception as e:
            print(f"## Cache lookup error: {e}")
            import traceback
            traceback.print_exc()
            
        return None

    def add(self, query_vector: List[float], query: str, result: Dict, context_hash: str = None):
        """Add new entry to cache"""
        # Ensure list
        if hasattr(query_vector, 'tolist'):
            query_vector = query_vector.tolist()
            
        self.vectors.append(query_vector)
        self.entries.append({
            "original_query": query,
            "result": result,
            "context_hash": context_hash
        })
        
        self._unsaved_changes += 1
        if self.auto_save and self._unsaved_changes >= 5: # Auto save every 5 new entries
            self.save()
