import sys
import os
import re
import time
import json
import threading
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.getcwd())

import requests
import numpy as np
import pandas as pd
import qdrant_client
from qdrant_client import models
from tqdm import tqdm
import bs4
import torch

# Project imports
from src import load_llm_config
from src.rag.prompts.builder import MathPromptBuilder
from src.rag.postprocessor import VNPTAI_PostProcessor
from src.guardrails.layer import ContentGuardrails
from src.functional.refusal import RefusalDetector
from src.functional.verifier import AnswerVerifier
from src.rag.correction import CorrectionBank, QuotaExhaustedException
from src.rag.cache import SemanticQACache
from src.function_calling.tools import ToolRegistry
from src.functional.optimizer import QuotaOptimizer, ExampleMetrics
from src.functional.rate_limiter import RateLimiter
from src.functional.common import normalize_answer_to_letter
from src.functional.constants import API_URL, API_URL_SMALL
from src.functional.logger import get_inference_logger
from src.rag.intention import VNPTAI_KNOWLEDGE_BASE
from src.etl.embedders import VNPTAIEmbedder
from src.function_calling.handlers import RAGHandler

# Optional/Lazy imports
try:
    from src.rag.intention.router import IntentRouter
    _ROUTER_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] IntentRouter not available (missing dependencies?): {e}")
    _ROUTER_AVAILABLE = False
    
    class IntentRouter:
        def __init__(self, *args, **kwargs): pass
        def route(self, query):
            return {
                'strategy': 'direct',
                'category': 'General',
                'complexity': {'score': 0.5},
                'tools': [],
                'metadata': {}
            }

try:
    from src.rag.correction_qdrant import CorrectionBankQdrant
except ImportError:
    CorrectionBankQdrant = None
    print("[SETUP FAILED] CorrectionBankQdrant not available (missing qdrant-client/numpy)")

_GLOBAL_ROUTER = None
_GLOBAL_GUARDRAILS = None


class VNPTAI_QA:
    """
    QA System with strict LLM call limits:
    - 1 Small LLM call: Tool selection
    - 1 Large LLM call: Final answer generation
    """
    
    def __init__(
        self,
        intent_model_path: str = "./models/intent/complex_dual_task",
        rag_collection: str = "360_xinchao",
        enable_guardrails: bool = True,
        toxicity_model_path: str = "./models/guardrails/toxicity",
        use_qdrant_correction: bool = True  # Use Qdrant for CorrectionBank (like RAG)
    ):
        global _GLOBAL_ROUTER, _GLOBAL_GUARDRAILS
        
        self.file_lock = threading.Lock()
        self.submission_csv = "submission.csv"
        self.submission_time_csv = "submission_time.csv"
        
        # Initialize CSV file with header if not exists
        if not os.path.exists(self.submission_csv):
            with open(self.submission_csv, 'w', encoding='utf-8') as f:
                f.write("id,answer\n")
                
        if not os.path.exists(self.submission_time_csv):
            with open(self.submission_time_csv, 'w', encoding='utf-8') as f:
                f.write("id,answer,time\n")

        # Initialize structured logger
        self.logger = get_inference_logger("logs/inference.txt")
            
        # Load LLM configs
        self.small_llm_config = load_llm_config('small')
        self.large_llm_config = load_llm_config('large')
        
        # Initialize Guardrails (cached)
        self.enable_guardrails = enable_guardrails
        if enable_guardrails:
            if _GLOBAL_GUARDRAILS is None:
                print("[INFO] Loading Guardrails model (First time)...")
                _GLOBAL_GUARDRAILS = ContentGuardrails(
                    enable_toxicity=True,
                    enable_pii=False,
                    enable_secrets=False,
                    toxicity_model_path=toxicity_model_path
                )
            self.guardrails = _GLOBAL_GUARDRAILS
        else:
            self.guardrails = None
        
        # Embedder (lightweight API client)
        self.embedder = VNPTAIEmbedder(model_name="vnptai_hackathon_embedding")
        self.refusal_detector = RefusalDetector(self.embedder)
        
        # Initialize Router
        if _ROUTER_AVAILABLE:
            if _GLOBAL_ROUTER is None:
                print(f"🧠 Loading Intent Router ({intent_model_path})...")
                _GLOBAL_ROUTER = IntentRouter(model_path=intent_model_path)
            self.router = _GLOBAL_ROUTER
        else:
            self.router = IntentRouter()

        # Verifier (Safety + Logic Refinment)
        # Pass initialized components to share resources
        self.verifier = AnswerVerifier(
            router=self.router,
            guardrails=self.guardrails,
            embedder=self.embedder,
            refusal_detector=self.refusal_detector
        )
        
        # RAG handler (lazy load)
        self._rag_handler = None
        self._rag_collection = rag_collection
        
        # Cache with auto-save
        self.cache = SemanticQACache(cache_file="dataset/semantic_cache.pkl", auto_save=True)
        
        # CorrectionBank for error-based learning
        # Use Qdrant for persistent storage and efficient vector search (like RAG)
        self.use_qdrant_correction = use_qdrant_correction
        
        if use_qdrant_correction and CorrectionBankQdrant is not None:
            self.correction_bank = CorrectionBankQdrant(
                qdrant_path="./qdrant_data",
                embedder=self.embedder
            )
        else:
            if use_qdrant_correction:
                print("[WARN] CorrectionBankQdrant requested but unavailable. Falling back to pickle.")
            self.correction_bank = CorrectionBank(rules_file="dataset/correction_rules.pkl")
        
        # LLM call counters (reset per query)
        self.small_llm_calls = 0
        self.large_llm_calls = 0
        
        # Rate Limiters (Safety buffer: 60->58, 40->38)
        self.small_limiter = RateLimiter(max_calls_per_hour=58)
        self.large_limiter = RateLimiter(max_calls_per_hour=38)

        # Prompt Builders
        self.prompt_builder = MathPromptBuilder()
    
    @property
    def rag_handler(self):
        """Lazy load RAG handler"""
        if self._rag_handler is None:
            # Note: RAGHandler is still in function_calling/handlers.py for now, or moved?
            self._rag_handler = RAGHandler(collection_name=self._rag_collection)
        return self._rag_handler
    
    def _check_rate_limit(self, resp: requests.Response, model_type: str = "Unknown"):
        """
        Check response for rate limit error.
        Raises QuotaExhaustedException to trigger wait + retry same sample.
        """
        # Case 1: HTTP 401/429
        if resp.status_code in [401, 429]:
            print(f"[WARN] HTTP {resp.status_code} detected -> Rate limit for {model_type}")
            raise QuotaExhaustedException(model_type, 1.0)
        
        # Case 2: Check response body for 'error' key
        if resp.status_code != 200:
            try:
                body = resp.json()
                error_msg = body.get('error', '')
                if error_msg:
                    error_lower = error_msg.lower() if isinstance(error_msg, str) else str(error_msg).lower()
                    if 'rate limit' in error_lower or 'quota' in error_lower:
                        print(f"[WARN] Rate limit detected in response body: {error_msg}")
                        raise QuotaExhaustedException(model_type, 1.0)
            except (json.JSONDecodeError, ValueError):
                pass

    def inference(self, dataset: List[Dict]) -> List[Dict]:
        """
        Main Entry for Scheduled Processing (Unified Strategy)
        Strategy:
        1. Unified Loop (No Phase A/B)
        2. Tool Selection: Rule-based
        3. Branching:
           - Reading/General/LongContext:
             - Try RAG. 
             - If RAG Score > 0.5: Use Context -> Small Answer (Skip Large Think).
             - Else: Large Think -> Small Answer.
           - MathLogic/Correctness:
             - Large Think -> Small Answer (n=3, temp=1.2) -> Voting.
        4. Safety: Toxicity Check > 0.5 -> Force Refusal.
        5. Quota: Sleep 1h on 401.
        """
        all_results = []
        total_items = len(dataset)
        processed_count = 0
        
        print(f"\n[INFO] Starting Unified Inference: {total_items} items")
        
        # Main Loop
        idx = 0
        try:
             # Try using it as a class/function (mock or standard 'from tqdm import tqdm')
             pbar = tqdm(total=total_items, desc="Processing")
        except TypeError:
             # Fallback if it is a module (standard 'import tqdm')
             pbar = tqdm.tqdm(total=total_items, desc="Processing")
        
        while idx < total_items:
            item = dataset[idx]
            qid = item.get('qid')
            # Update description only if real tqdm
            pbar.set_description(f"Processing {qid}")
            query = item.get('question')
            choices = item.get('choices', [])
            
            # Log question start
            self.logger.log_question_start(qid, query, choices)
            
            start_time = time.time()
            total_sleep = 0.0
            thinking_content = ""  # Track thinking for logging
            
            try:
                # print(f"\nProcessing {idx+1}/{total_items}: {qid}") # pbar handles this
                
                # 1. Rule-Based Tool Selection
                # Default to General so we don't accidentally trigger Math logic if router missing
                default_routing = {'tools': ['search_knowledge_base'], 'metadata': {}, 'category': 'General', 'probs': {}}
                
                routing = self.router.route(query) if _ROUTER_AVAILABLE else default_routing
                tool_call = self._select_tool_rule_based(query, routing)
                
                context = None
                category = routing.get('category', 'General')
                final_answer = "Error"
                
                # Log intent routing
                tools = routing.get('tools', [])
                probs = routing.get('probs', {})
                self.logger.log_intent_routing(qid, category, tools, probs)
                
                # --- SAFETY / REFUSAL CHECK (Strict) ---
                refusal_prob = routing.get('probs', {}).get('Refusal', 0.0)
                unsafe_keywords = ["chống phá", "tham nhũng", "lợi dụng", "phá hoại", "gây hại", "gây thương tích"]
                
                is_unsafe_content = False
                toxicity_score = None
                
                # Check 1: Category Match
                if category == 'Refusal':
                    is_unsafe_content = True
                    print(f"   [STOP] Safety Trigger: Category is Refusal")
                    
                # Check 2: Probability + Keywords
                elif refusal_prob > 0.2:
                    query_lower = query.lower()
                    if any(kw in query_lower for kw in unsafe_keywords):
                        is_unsafe_content = True
                        print(f"   [STOP] Safety Trigger: Refusal Prob {refusal_prob:.2f} + Keyword match")
                
                # Log toxicity check
                self.logger.log_toxicity_check(qid, is_unsafe_content, toxicity_score, refusal_prob)
                
                if is_unsafe_content:
                    refusal_choice = self.refusal_detector.detect(choices)
                    if refusal_choice:
                        print(f"   [STOP] Forced Refusal: {refusal_choice}")
                        final_answer = refusal_choice
                        
                        # Log calling flow for refusal
                        self.logger.log_calling_flow(qid, "SAFETY_REFUSAL", {"reason": "toxicity_detected"})
                        self.logger.log_final_answer(qid, final_answer, final_answer, duration=time.time()-start_time)
                        self.logger.log_question_complete(qid)
                        
                        # Skip LLM
                        duration = round(time.time() - start_time, 2)
                        res = {"qid": qid, "answer": final_answer, "time": duration}
                        all_results.append(res)
                        self._save_sample_result(res)
                        idx += 1
                        pbar.update(1)
                        continue
                
                # BRANCH A: Reading / General / LongContext
                # Logic: Check RAG first. If good, skip think.
                if category in ['ReadingComprehension', 'LongContext', 'General']:
                    is_rag_good = False
                    
                    # Execute Tool (RAG or Embedded)
                    tool_name = tool_call.get('function', {}).get('name') if tool_call else ''
                    
                    if tool_name == 'search_knowledge_base':
                        context_result = self._execute_tool_no_llm(tool_call, query, routing)
                        rag_score = context_result.get('metadata', {}).get('max_score', 0.0)
                        
                        if rag_score > 0.5:
                            context = context_result
                            is_rag_good = True
                            print(f"   [RAG] High Score ({rag_score:.2f}) -> Skipping Large Think")
                            
                            # Log RAG context
                            snippet = context_result.get('content', '')[:200] if context_result.get('content') else None
                            self.logger.log_rag_context(qid, "RAG_HIGH_SCORE", rag_score, snippet)
                        else:
                            print(f"   [RAG] Low Score ({rag_score:.2f}) -> Fallback to Large Think")
                            self.logger.log_rag_context(qid, "RAG_LOW_SCORE", rag_score)
                            context = None # Don't use bad context
                            
                    elif tool_name == 'use_embedded_context':
                        # Execute embedded extraction
                        context_result = self._execute_tool_no_llm(tool_call, query, routing)
                        context = context_result
                        is_rag_good = True # Embedded context is always considered "good"/authoritative
                        print(f"   [RAG] Embedded Context Extracted -> Skipping Large Think")
                        
                        snippet = context_result.get('content', '')[:200] if context_result.get('content') else None
                        self.logger.log_rag_context(qid, "EMBEDDED_CONTEXT", 1.0, snippet)
                    
                    if is_rag_good:
                        # Path 1: RAG -> Small Answer (Cost: 0 Large, 1 Small)
                        print("   [>>] Direct Small Answer (RAG-based)")
                        self.logger.log_calling_flow(qid, "RAG_DIRECT_SMALL", {"llm_calls": "1_small"})
                        
                        total_sleep += self.small_limiter.wait_if_needed(1)
                        final_answer = self._call_small_answer(query, context, choices, thinking=None)
                    else:
                        # Path 2: Large Think -> Small Answer (Cost: 1 Large, 1 Small)
                        print(f"   [THINK] Reasoning ({qid})...")
                        self.logger.log_calling_flow(qid, "LARGE_THINK_SMALL_ANSWER", {"llm_calls": "1_large_1_small"})
                        
                        total_sleep += self.large_limiter.wait_if_needed(1)
                        thinking_content, _ = self._call_large_think_only(query, context, choices)
                        
                        # Log thinking content
                        self.logger.log_thinking_content(qid, thinking_content, "Large")
                        
                        print("   📝 Generating Answer...")
                        total_sleep += self.small_limiter.wait_if_needed(1)
                        final_answer = self._call_small_answer(query, context, choices, thinking=thinking_content)

                # BRANCH B: MathLogic / Correctness
                # Logic: Always Think. High Temp Voting.
                else:
                    # Execute Tool (Math) if needed (for prompts)
                    if tool_call and tool_call.get('function', {}).get('name') == 'solve_math_problem':
                         context_result = self._execute_tool_no_llm(tool_call, query, routing)
                         context = context_result
                    
                    # Log calling flow
                    self.logger.log_calling_flow(qid, "MATH_VOTING_3LLM", {
                        "llm_calls": "1_large_3_small",
                        "temperature": 1.2,
                        "strategy": "voting"
                    })
                    
                    # Large Think
                    print(f"   [THINK] Reasoning ({qid})...")
                    total_sleep += self.large_limiter.wait_if_needed(1)
                    thinking_content, _ = self._call_large_think_only(query, context, choices)
                    
                    # Log thinking content
                    self.logger.log_thinking_content(qid, thinking_content, "Large")
                    
                    # Small Answer (n=3, temp=1.2)
                    print("   [VOTE] Math Voting (n=3, temp=1.2)...")
                    total_sleep += self.small_limiter.wait_if_needed(1)
                    small_answers = self._call_small_answer_n3(query, context, choices, thinking_content, temperature=1.2)
                    
                    if small_answers:
                        final_answer = Counter(small_answers).most_common(1)[0][0]
                        print(f"      [RESULT] Votes: {small_answers} -> Final: {final_answer}")
                        
                        # Log voting results
                        self.logger.log_voting_results(qid, small_answers, final_answer, 1.2)
                    else:
                        print("      [WARN] No valid answers from Small LLM")
                        final_answer = "Error"

                # 5. Final Verification (Safety + Format + Ambiguity)
                # This replaces the ad-hoc toxicity check and refusal finding above
                # And adds the fuzzy logic/embedding fallback from post_inference
                
                # Check legacy code removal: I should comment out or remove the old guardrails block if verifier handles it.
                # But to be safe and clean, I will just let Verifier handle the final "polish".
                # The verifier checks safety again, so even if we missed it above (we shouldn't have due to updates), it catches it.
                
                final_verified = self.verifier.verify(query, choices, final_answer, qid=qid)
                
                # Timing
                end_time = time.time()
                duration = round(end_time - start_time - total_sleep, 2)
                if duration < 0: duration = 0.0
                
                # Log final answer
                self.logger.log_final_answer(qid, final_answer, final_verified, duration=duration)
                self.logger.log_question_complete(qid)
                
                # Log
                print(f"   [OK] Answer: {final_verified} (Time: {duration}s)")
                
                res = {
                    "qid": qid, 
                    "answer": final_verified,
                    "time": duration
                }
                all_results.append(res)
                self._save_sample_result(res)
                
                # Move to next item
                idx += 1
                pbar.update(1)
                
            except QuotaExhaustedException as e:
                self.logger.log_quota_exhausted(qid, e.model_type, e.wait_minutes)
                print(f"\n[WAIT] RATE LIMIT ({e}). Sleeping 1 hour before retrying item {qid}...")
                for _ in tqdm(range(60), desc="Quota Reset Wait (mins)"):
                    time.sleep(60)  # Wait 60 minutes total (1 hour)
                    total_sleep += 60.0
                print("[RESUME] Resuming same item...")
                # Do NOT increment idx, retry same item
                
            except Exception as e:
                self.logger.log_error(qid, e, "inference mode")
                print(f"[ERR] Error processing {qid}: {e}")
                # Create error result to keep moving
                # res = {"qid": qid, "answer": "Error"}
                # self._save_sample_result(res)
                idx += 1
                pbar.update(1)
                    
        pbar.close()
        return all_results


    def _call_large_think_only(self, query: str, context: Any, choices: List[str]) -> Tuple[str, float]:
        """Generate <think> content only"""
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        # Simplified 3-step prompt for faster inference
        sys_prompt = (
            "Bạn là chuyên gia. Nhiệm vụ: Suy luận kỹ càng, chính xác.\n"
            "QUY TRÌNH (3 BƯỚC):\n"
            "1. PHÂN TÍCH: Xác định loại bài toán, dữ kiện quan trọng\n"
            "2. GIẢI QUYẾT: Thực hiện các bước tính toán/suy luận\n"
            "3. KIỂM TRA: Xác minh đáp án có hợp lý không\n"
            "OUTPUT: <think> [Suy luận kỹ càng] </think>\n"
            "LƯU Ý: CHỈ suy luận, KHÔNG đưa ra đáp án cuối."
        )
        
        # Inject Context if available
        context_str = ""
        if context and context.get('content'):
            context_str = f"\n--- THÔNG TIN THAM KHẢO ---\n{context['content']}\n---------------------------\n"
            
        user_msg = f"Câu hỏi: {query}\nCác lựa chọn:\n{choices_str}\n{context_str}\nHãy suy luận:"
        
        headers = self._build_headers(self.large_llm_config)
        data = {
            'model': 'vnptai_hackathon_large',
            'messages': [ {'role':'system', 'content': sys_prompt}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 512,  # Reduced from 1024 for speed
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 20,
            'stop': ['</think>']
        }
        try:
            resp = requests.post(API_URL, headers=headers, json=data, timeout=30)  # Reduced from 60s
            self._check_rate_limit(resp, "Large")  # Check rate limit (HTTP + body)
            if resp.status_code == 200:
                raw = self._extract_content(resp.json())
                match = re.search(r'<think>(.*?)</think>', raw, re.DOTALL | re.IGNORECASE)
                if match: return match.group(1).strip(), 0.0
                return raw, 0.0
            return "", 0.0
        except QuotaExhaustedException: raise
        except Exception as e:
            print(f"[ERR] Large Think Error: {e}")
            return "", 0.0

    def _call_small_answer_n3(self, query: str, context:Any, choices: List[str], thinking: str, temperature: float = 0.7) -> List[str]:
        """
        Call Small LLM with Perspective Voting (3 distinct personas).
        Returns list of 3 answers.
        """
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        
        # 3 Personas for Diversity
        personas = [
            ("Judge", "Bạn là Giám khảo công tâm. Dựa trên suy luận, hãy chọn đáp án đúng nhất (JSON)."),
            ("Skeptic", "Bạn là Người Phản Biện khó tính. Hãy nghi ngờ suy luận trên, tìm kẽ hở, và cẩn trọng chọn đáp án đúng nhất (JSON)."),
            ("Verify Expert", "Bạn là Verify Expert. Hãy đối chiếu suy luận với kiến thức nền tảng trong ngữ cảnh để tránh bị 'ảo giác'. Chọn đáp án (JSON).")
        ]
        
        answers = []
        # Parallel Execution
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_role = {
                executor.submit(self._call_small_single, p[1], query, choices_str, thinking, temperature): p[0]
                for p in personas
            }
            
            for future in as_completed(future_to_role):
                role = future_to_role[future]
                try:
                    res = future.result()
                    if res:
                        norm = normalize_answer_to_letter(res, choices)
                        if norm:
                            answers.append(norm)
                except Exception as e:
                    print(f"[WARN] Small {role} Failed: {e}")
                
        return answers

    def _call_small_single(self, sys_prompt: str, query: str, choices_str: str, thinking: str, temperature: float) -> Optional[str]:
        """Helper for parallel execution"""
        user_msg = f"Câu hỏi: {query}\nLựa chọn:\n{choices_str}\n\n--- SUY LUẬN ---\n{thinking}\n--- HẾT ---\n\nĐáp án JSON: {{\"answer\": \"X\"}}"
        
        headers = self._build_headers(self.small_llm_config)
        data = {
            'model': 'vnptai_hackathon_small',
            'messages': [ {'role':'system', 'content': sys_prompt}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 64,  # Reduced from 128 (only need letter)
            'temperature': temperature, 
            'n': 1,
            'top_p': 0.8,
            'top_k': 20
        }
        
        try:
            resp = requests.post(API_URL_SMALL, headers=headers, json=data, timeout=15)  # Reduced from 40s
            self._check_rate_limit(resp, "Small")
            if resp.status_code == 200:
                rjson = resp.json()
                if 'choices' in rjson:
                    content = rjson['choices'][0].get('message', {}).get('content', '')
                    return content # Return raw content, normalize outside
        except QuotaExhaustedException: raise
        except Exception: raise
        return None


    def _call_large_review_vote(self, query: str, context:Any, choices: List[str], thinking: str, small_answers: List[str]) -> str:
        """Large LLM reviews thinking + small answers and gives its own weighted vote"""
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        sys_prompt = "Bạn là Trưởng Ban Giám Khảo. Hãy xem xét suy luận và các dự đoán của trợ lý để đưa ra quyết định cuối cùng."
        
        user_msg = f"Câu hỏi: {query}\nLựa chọn:\n{choices_str}\n\n--- SUY LUẬN GỐC ---\n{thinking}\n\n"
        if small_answers:
            user_msg += f"--- DỰ ĐOÁN TRỢ LÝ ---\n{small_answers}\n"
            
        user_msg += "\nQuyết định của bạn là gì? Format: {\"answer\": \"X\"}"
        
        headers = self._build_headers(self.large_llm_config)
        data = {
            'model': 'vnptai_hackathon_large',
            'messages': [ {'role':'system', 'content': sys_prompt}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 128,
            'temperature': 0.2
        }
        try:
            resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
            self._check_rate_limit(resp, "Large")  # Check rate limit
            if resp.status_code == 200:
                return normalize_answer_to_letter(self._extract_content(resp.json()), choices)
            return "Error"
        except QuotaExhaustedException:
            raise  # Re-raise to trigger wait + retry
        except Exception as e:
            print(f"[ERR] Large Review Vote Error: {e}")
            return "Error"

    def _call_large_direct(self, query: str, choices: List[str]) -> str:
        """Single shot Think + Answer"""
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        sys_prompt = "Bạn là chuyên gia. Suy luận và trả lời câu hỏi."
        user_msg = (
            f"Câu hỏi: {query}\nLựa chọn:\n{choices_str}\n\n"
            "Output Format:\n<think>...</think>\n{\"answer\": \"X\"}"
        )
        
        headers = self._build_headers(self.large_llm_config)
        data = {
            'model': 'vnptai_hackathon_large',
            'messages': [ {'role':'system', 'content': sys_prompt}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 512,
            'temperature': 0.5
        }
        try:
            resp = requests.post(API_URL, headers=headers, json=data, timeout=60)
            self._check_rate_limit(resp, "Large")  # Check rate limit
            if resp.status_code == 200:
                raw = self._extract_content(resp.json())
                return normalize_answer_to_letter(raw, choices)
            return "Error"
        except QuotaExhaustedException:
            raise  # Re-raise to trigger wait + retry
        except Exception as e:
            print(f"[ERR] Large Direct Error: {e}")
            return "Error"

    def _call_small_answer(self, query: str, context:Any, choices: List[str], thinking: Optional[str]) -> str:
        """Small LLM converts Thinking to JSON Answer"""
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        
        sys_prompt = "Bạn là trợ lý tổng hợp. Nhiệm vụ: Chốt đáp án đúng duy nhất dưới dạng JSON."
        
        user_msg = f"Câu hỏi: {query}\nLựa chọn:\n{choices_str}\n"
        if thinking:
            user_msg += f"\n--- SUY LUẬN TỪ CHUYÊN GIA ---\n{thinking}\n--- HẾT ---\n"
        
        user_msg += "\nHãy chốt đáp án JSON: {\"answer\": \"X\"}"
        
        headers = self._build_headers(self.small_llm_config)
        data = {
            'model': 'vnptai_hackathon_small',
            'messages': [ {'role':'system', 'content': sys_prompt}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 64,  # Reduced from 128
            'temperature': 0.3
        }
        
        try:
            resp = requests.post(API_URL_SMALL, headers=headers, json=data, timeout=20)  # Reduced from 30s
            self._check_rate_limit(resp, "Small")  # Check rate limit
            if resp.status_code == 200:
                return self._extract_content(resp.json())
            return "Error"
        except QuotaExhaustedException:
            raise  # Re-raise to trigger wait + retry
        except Exception as e:
            print(f"[ERR] Small Answer Error: {e}")
            return "Error"

    def _call_large_answer_using_think(self, query: str, context:Any, choices: List[str], thinking: str) -> str:
        """Large LLM Final Answer for Hardest Items using PREVIOUS Thinking"""
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        
        sys_prompt = "Bạn là chuyên gia thẩm định. Dựa trên suy luận (của chính bạn trước đó), hãy chốt đáp án CHÍNH XÁC NHẤT."
        
        user_msg = f"Câu hỏi: {query}\nLựa chọn:\n{choices_str}\n"
        user_msg += f"\n--- SUY LUẬN ---\n{thinking}\n--- HẾT ---\n"
        user_msg += "\nFormat: {\"answer\": \"X\"}"
        
        headers = self._build_headers(self.large_llm_config)
        data = {
            'model': 'vnptai_hackathon_large',
            'messages': [ {'role':'system', 'content': sys_prompt}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 128,
            'temperature': 0.3,
            'top_p': 0.8,
            'top_k': 20,
        }
        
        try:
            resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
            self._check_rate_limit(resp, "Large")  # Check rate limit
            if resp.status_code == 200:
                raw = self._extract_content(resp.json())
                return raw # Should be JSON
            return "Error"
        except QuotaExhaustedException:
            raise  # Re-raise to trigger wait + retry
        except Exception as e:
            print(f"[ERR] Large Hard-Retry Error: {e}")
            return "Error"

    def _save_sample_result(self, result: Dict):
        """Thread-safe append to prediction.csv"""
        if not self.file_lock: return
        
        with self.file_lock:
            try:
                import csv
                # Append row to submission.csv
                with open(self.submission_csv, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        result.get('qid', ''),
                        result.get('answer', '')
                    ])
                    
                # Append row to submission_time.csv
                with open(self.submission_time_csv, 'a', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        result.get('qid', ''),
                        result.get('answer', ''),
                        result.get('time', '')
                    ])
                    
            except Exception as e:
                print(f"[WARN] Failed to save sample: {e}")

    def _call_small_reasoning(self, query: str, choices: List[str]) -> Tuple[str, str, str]:
        """
        Use Small LLM to generate Chain-of-Thought reasoning.
        Returns: (full_response, extracted_thinking, draft_answer)
        """
        self.small_limiter.wait_if_needed()
        
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        
        prompt = (
            f"Câu hỏi: {query}\n"
            f"Các lựa chọn:\n{choices_str}\n\n"
            "Hãy suy luận từng bước để tìm đáp án đúng.\n"
            "FORMAT:\n"
            "1. <think> ... phân tích ... </think>\n"
            "2. <answer>X</answer> với X là A/B/C/D/E/F/G/H/I hoặc K (alphabet format)\n"
        )
        
        headers = self._build_headers(self.small_llm_config)
        data = {
            'model': 'vnptai_hackathon_small',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_completion_tokens': 768,
            'temperature': 0.7,
            'top_k': 20,
            'n': 1
        }
        
        try:
            resp = requests.post(API_URL_SMALL, headers=headers, json=data, timeout=40)
            if resp.status_code == 200:
                content = self._extract_content(resp.json())
                print("   📤 Small raw content reasoning: \n", content[:200], "...")
                # Extract <thinking> tag
                extracted_thinking = ""
                thinking_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL | re.IGNORECASE)
                if thinking_match:
                    extracted_thinking = thinking_match.group(1).strip()
                
                # Extract <answer> tag
                draft_answer = ""
                answer_match = re.search(r'<answer>\s*([A-Ea-e])\s*</answer>', content, re.IGNORECASE)
                if answer_match:
                    draft_answer = answer_match.group(1).upper()
                
                print(f"   📝 Small: {len(content)} chars, thinking={len(extracted_thinking)}, draft={draft_answer}")
                return (content, extracted_thinking, draft_answer)
            return ("", "", "")
        except Exception as e:
            print(f"[WARN] Small error: {e}")
            return ("", "", "")
            
    def _call_large_verifier(self, query: str, choices: List[str], reasoning_list: List[Tuple[str, str, str]]) -> str:
        """
        Use Large LLM to verify reasoning and conclude.
        reasoning_list: List of (full_response, extracted_thinking, draft_answer)
        """
        self.large_limiter.wait_if_needed()
        
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        
        # Build context from ALL reasoning - use extracted_thinking if available, else full_response
        context_block = ""
        draft_answers = []
        
        for idx, reasoning_tuple in enumerate(reasoning_list):
            if not reasoning_tuple or len(reasoning_tuple) != 3:
                continue
            
            full_response, extracted_thinking, draft_answer = reasoning_tuple
            
            # Use extracted_thinking if available, otherwise use full_response
            reasoning_content = extracted_thinking if extracted_thinking else full_response
            
            if reasoning_content and len(reasoning_content.strip()) > 10:
                context_block += f"=== Luồng suy luận {idx+1} ===\n{reasoning_content}\n"
                if draft_answer:
                    context_block += f"Dự đoán: {draft_answer}\n"
                    draft_answers.append(draft_answer)
                context_block += "\n"
        
        # Analyze draft answer consensus
        consensus_note = ""
        if draft_answers:
            counter = Counter(draft_answers)
            most_common = counter.most_common(1)[0]
            if len(draft_answers) > 1:
                if most_common[1] == len(draft_answers):
                    consensus_note = f"\n[Tất cả {len(draft_answers)} luồng đều chọn {most_common[0]} - cần kiểm tra kỹ]\n"
                else:
                    consensus_note = f"\n[Các dự đoán: {dict(counter)} - cần thẩm định]\n"
        
        # Build prompts based on whether we have reasoning or not
        if context_block.strip():
            system_prompt = (
                "Bạn là chuyên gia thẩm định. Nhiệm vụ:\n"
                "1. Đọc các luồng suy luận tham khảo (có thể đúng hoặc sai)\n"
                "2. Phát hiện lỗi logic nếu có\n"
                "3. Đưa ra đáp án CHÍNH XÁC\n\n"
                "QUY TẮC OUTPUT:\n"
                "- Format: {\"answer\": \"X\"} với X là A/B/C/D/E/F/G/H/I hoặc K (alphabet format)\n"
                "- CHỈ trả chữ cái, KHÔNG viết 'Câu trả lời thứ C'"
            )
            user_prompt = (
                f"Câu hỏi: {query}\n\n"
                f"Các lựa chọn:\n{choices_str}\n\n"
                f"--- THAM KHẢO ---\n{context_block}{consensus_note}--- HẾT ---\n\n"
                "Đáp án đúng là gì? JSON: {\"answer\": \"X\"}"
            )
        else:
            # No reasoning available - direct mode
            print("No reasoning, using direct mode")
            system_prompt = (
                "Phân tích câu hỏi và đưa ra đáp án CHÍNH XÁC.\n"
                "Format: {\"answer\": \"X\"} với X là A/B/C/D/E/F/G/H/I hoặc K (alphabet format)"
            )
            user_prompt = (
                f"Câu hỏi: {query}\n\n"
                f"Các lựa chọn:\n{choices_str}\n\n"
                "Đáp án: {\"answer\": \"X\"}"
            )
        
        headers = self._build_headers(self.large_llm_config)
        data = {
            'model': 'vnptai_hackathon_large',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'max_completion_tokens': 512,
            'temperature': 0.3,
            'top_k': 20,
            'n': 1
        }
        
        try:
            resp = requests.post(API_URL, headers=headers, json=data, timeout=60)
            if resp.status_code == 200:
                raw = self._extract_content(resp.json())
                print(f"   📤 Large raw: {raw[:80]}...")
                return raw
            return '{"answer": "Error"}'
        except Exception as e:
            print(f"   ❌ Large error: {e}")
            return '{"answer": "Error"}'
    
    
    def _call_small_llm_once(self, query: str, routing: Dict) -> Optional[Dict]:
        """
        Small LLM: Tool selection ONLY
        Returns tool_call or None
        """
        if self.small_llm_calls > 1000000: # Safety cap only
            print("[WARN] Small LLM calls excessive")
            return None
        
        # Enforce Rate Limit
        self.small_limiter.wait_if_needed()
        
        tools = self._get_tool_schemas(routing['tools'])
        
        if not tools:
            return None
        
        headers = self._build_headers(self.small_llm_config)
        
        json_data = {
            'model': 'vnptai_hackathon_small',
            'messages': [{'role': 'user', 'content': query}],
            'tools': tools,
            'tool_choice': 'auto',
            'temperature': 0.3,
            'max_completion_tokens': 256 # Increased from 64 for safety
        }
        
        try:
            response = requests.post(
                API_URL_SMALL, 
                headers=headers, 
                json=json_data, 
                timeout=30
            )
            response.raise_for_status()
            self.small_llm_calls += 1
            
            result = response.json()
            return self._extract_tool_call(result)
            
        except requests.exceptions.HTTPError as e:
            self.small_llm_calls += 1
            
            status_code = e.response.status_code if e.response else "Unknown"
            error_body = e.response.text[:500] if e.response else "No response body"
            
            print(f"\n❌ Small LLM HTTP Error {status_code}:")
            print(f"   URL: {API_URL_SMALL}")
            print(f"   Response: {error_body}")
            
            if status_code == 401:
                print(f"\n🚨 401 Unauthorized (Quota/Auth) in Small LLM (Tool Selection)")
                raise QuotaExhaustedException("Small", 60.0)

            if status_code == 403:
                print(f"\n🚨 AUTHENTICATION FAILED (403 Forbidden)!")
                raise

            # User specific: Treat "No response body" or unknown errors as potentially Quota Exhausted
            if "No response body" in error_body or not error_body.strip():
                 print(f"\n🚨 Empty Response Body detected (Likely Quota Exhausted). Triggering sleep.")
                 raise QuotaExhaustedException("Small", 60.0)
            
            return None
            
        except Exception as e:
            print(f"[WARN] Small LLM error: {e}")
            self.small_llm_calls += 1
            return None
    
    def _execute_tool_no_llm(
        self, 
        tool_call: Dict, 
        query: str,
        routing: Dict
    ) -> Dict:
        """
        Execute tool WITHOUT calling LLM
        Returns context/prompt for Large LLM
        """
        tool_name = tool_call.get('function', {}).get('name', '')
        
        try:
            args_str = tool_call.get('function', {}).get('arguments', '{}')
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
        except:
            args = {}
        
        print(f"🔧 Executing tool: {tool_name}")
        
        if tool_name == 'solve_math_problem':
            # MathPromptBuilder builds prompt, doesn't solve
            problem_type = routing['metadata'].get('problem_type', 'math')
            given_options = args.get('given_options', None)
            
            math_messages = self.prompt_builder.build_messages(
                problem_statement=args.get('problem_statement', query),
                problem_type=problem_type,
                given_options=given_options
            )
            
            return {
                'type': 'math_messages',
                'content': math_messages,
                'metadata': routing['metadata']
            }
        
        elif tool_name == 'search_knowledge_base':
            # RAG retrieves context (NO LLM)
            top_k = routing['metadata'].get('top_k', 10)
            min_score = routing['metadata'].get('min_score', 0.5) # Default 0.5
            
            rag_result = self.rag_handler.search(
                query=args.get('query', query),
                top_k=top_k,
                min_score=min_score
            )
            
            if rag_result.get('found', False):
                print(f"✅ RAG Found {rag_result.get('num_results', 0)} docs.")
                scores = []
                for r in rag_result.get('results', [])[:1]:
                    s = r.get('score', 0.0)
                    scores.append(s)
                    print(f"   - Top doc: {r['metadata'].get('doc_title') or 'N/A'} ({s:.3f})")
                max_score = max(scores) if scores else 0.0
            else:
                print("[WARN] RAG returned no results.")
                max_score = 0.0
            
            return {
                'type': 'rag_context',
                'content': rag_result.get('context', ''),
                'metadata': {**routing['metadata'], 'max_score': max_score}
            }
        
        elif tool_name == 'use_embedded_context':
            # Extract embedded context using BM25
            
            full_text = args.get('full_text', query)
            extractor = VNPTAI_KNOWLEDGE_BASE(full_text)
            knowledge, clean_query = extractor.extract(query)
            
            return {
                'type': 'embedded_context',
                'content': knowledge,
                'metadata': routing['metadata']
            }
        
        else:
            return {
                'type': 'unknown',
                'content': '',
                'metadata': routing['metadata']
            }
    
    def _call_small_llm_for_answer(
        self,
        query: str,
        context: Optional[Dict],
        routing: Dict,
        correction_tip: Optional[str] = None,
        choices: Optional[List[str]] = None
    ) -> str:
        """
        Small LLM: Answer generation for training mode (distil.py)
        Saves Large LLM quota for Reflexion correction.
        """
        # Enforce Rate Limit
        self.small_limiter.wait_if_needed()
        
        # Build messages (same as Large LLM)
        messages = self._build_messages(query, context, routing, correction_tip, choices)
        
        headers = self._build_headers(self.small_llm_config)
        
        json_data = {
            'model': 'vnptai_hackathon_small',
            'messages': messages,
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 20,
            'n': 1,
            'max_completion_tokens': 512 # Increased for answers
        }
        
        try:
            response = requests.post(
                API_URL_SMALL,
                headers=headers,
                json=json_data,
                timeout=60
            )
            response.raise_for_status()
            self.small_llm_calls += 1
            
            result = response.json()
            return self._extract_content(result)
            
        except requests.exceptions.HTTPError as e:
            self.small_llm_calls += 1
            if e.response is not None and e.response.status_code == 401:
                print(f"\n🚨 401 Unauthorized (Quota/Auth) in Small LLM")
                raise QuotaExhaustedException("Small", 60.0)
            print(f"[WARN] Small LLM (answer) HTTP error: {e}")
            return "Error: Small LLM failed"

        except Exception as e:
            print(f"[WARN] Small LLM (answer) error: {e}")
            self.small_llm_calls += 1
            return "Error: Small LLM failed"
    
    def _call_large_llm_once(
        self,
        query: str,
        context: Optional[Dict],
        routing: Dict,
        correction_tip: Optional[str] = None,
        choices: Optional[List[str]] = None
    ) -> str:
        """
        Large LLM: Final answer generation (EXACTLY 1 call)
        """
        if self.large_llm_calls > 0:
            print("[WARN] Large LLM already called")
            return "Error: LLM limit exceeded"
        
        # Enforce Rate Limit
        self.large_limiter.wait_if_needed()
        
        # Build messages based on context type
        messages = self._build_messages(query, context, routing, correction_tip, choices)
        
        headers = self._build_headers(self.large_llm_config)
        
        json_data = {
            'model': 'vnptai_hackathon_large',
            'messages': messages,
            'temperature': 0.7, 
            'top_p': 0.8, 
            'top_k': 20, 
            'n': 1,
            'max_completion_tokens': 512 # Standard length for General queries
        }
        
        # Retry logic
        max_retries = 3
        backoff = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    API_URL,
                    headers=headers,
                    json=json_data,
                    timeout=60
                )
                response.raise_for_status()
                self.large_llm_calls += 1
                
                result = response.json()
                return self._extract_content(result)
                
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0
                
                # SPECIAL HANDLING FOR 401 (Quota/Auth) -> Wait 1 hour
                if status_code == 401:
                    print(f"\n🚨 401 Unauthorized (Quota/Auth) in Large LLM")
                    raise QuotaExhaustedException("Large", 60.0)
                
                # If 429 (Rate Limit) or 5xx (Server Error) -> Retry
                if status_code == 429 or status_code >= 500:
                    if attempt < max_retries - 1:
                        sleep_time = backoff * (2 ** attempt)
                        print(f"[WARN] API Error {status_code}. Retrying in {sleep_time}s... ({attempt+1}/{max_retries})")
                        time.sleep(sleep_time)
                        continue
                    else:
                        # Final failure
                        print(f"\n❌ Large LLM Failed after {max_retries} retries. Status: {status_code}")
                        error_body = e.response.text[:200] if e.response else ""
                        print(f"   Response: {error_body}")
                        return f"Error: HTTP {status_code}"
                
                # Other 4xx errors (400, 404) -> Don't retry
                print(f"❌ Large LLM Client Error {status_code}")
                return f"Error: HTTP {status_code}"
                
            except Exception as e:
                print(f"[WARN] Large LLM error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                self.large_llm_calls += 1
                return f"Error: {str(e)}"
        
        return "Error: Max retries exceeded"
    
    def _build_messages(
        self,
        query: str,
        context: Optional[Dict],
        routing: Dict,
        correction_tip: Optional[str] = None,
        choices: Optional[List[str]] = None
    ) -> List[Dict]:
        """Build message list for Large LLM"""
        
        # Prepare correction warning if available
        tip_warning = ""
        if correction_tip:
            tip_warning = f"\n\n[WARN] LƯU Ý QUAN TRỌNG: {correction_tip}"
            print(f"📖 Injecting correction tip into prompt")
        
        # Format choices as YAML list if present with Letters (A, B, C...)
        choice_suffix = ""

        if choices:
            formatted_choices = []
            
            # CONDITION: Strategy must be SAFE (not refusal)
            is_safe_query = (routing.get('strategy') != 'refusal')
            
            # Pre-scan choices to see if we have BOTH types of noise:
            # 1. Refusal-like ("không thể trả lời", "tôi không biết")
            # 2. Aggregation-like ("tất cả các đáp án", "cả a, b, c")
            has_refusal_option = False
            has_aggregation_option = False
            
            refusal_keywords = ["không thể trả lời", "không thể chia sẻ", "tôi không biết", "nằm ngoài phạm vi"]
            aggregation_keywords = ["tất cả các đáp án", "cả a, b, c", "cả 3 đáp án", "các đáp án trên"]
            
            for c in choices:
                c_lower = str(c).lower()
                if any(k in c_lower for k in refusal_keywords): has_refusal_option = True
                if any(k in c_lower for k in aggregation_keywords): has_aggregation_option = True
            
            # TRIGGER FILTER ONLY IF SAFE + HAS BOTH TYPES (User Requirement)
            should_filter = is_safe_query and (has_refusal_option and has_aggregation_option)

            for idx, choice in enumerate(choices):
                choice_str = str(choice).lower().strip()
                original_letter = chr(65 + idx)
                
                is_excluded = False
                if should_filter:
                     # Remove if it matches EITHER keyword set
                     if any(k in choice_str for k in refusal_keywords) or \
                        any(k in choice_str for k in aggregation_keywords):
                         is_excluded = True
                
                if not is_excluded:
                    formatted_choices.append(f"{original_letter}. {choice}")
            
            # Fallback: If map is empty (rare), revert to original
            if not formatted_choices:
                 formatted_choices = [f"{chr(65+i)}. {c}" for i, c in enumerate(choices)]
            
            yaml_list = "\n".join(formatted_choices)
            choice_suffix = f"\nLựa chọn 1 trong các phương án sau (chỉ trả phương án đúng):\n{yaml_list}\n"
        
        # Output instruction
        format_instr = (
            'Trả lời với format JSON duy nhất: {"answer": "<nội dung>"}\n'
            'Trong đó <nội dung> là nội dung CHÍNH XÁC của phương án đúng (không cần A,B,C,D).\n'
            'Với công thức toán, BẮT BUỘC dùng LaTeX chuẩn ($...$). '
            'VD: `\\frac{a}{b}` thay vì `rac{a}{b}`. KHÔNG dùng ký tự Unicode lạ.'
        )
        
        full_user_content = f"{query}{choice_suffix}\n{format_instr}{tip_warning}"

        if context and context['type'] == 'math_messages':
            # Math: context['content'] is a LIST of messages from prompt_builder
            # Append the final user query (with format instructions)
            messages = context['content']

            
            # Extract the last user message content
            last_content = messages[-1]['content']
            
            # Append our strict format instructions
            updated_content = f"{last_content}\n\n{choice_suffix}\n{format_instr}{tip_warning}"
            
            # Update the last message
            messages[-1]['content'] = updated_content
            
            return messages

        elif context and context['type'] == 'math_prompt':
             # Legacy support (should be removed eventually)
             return [
                {'role': 'system', 'content': context['content']},
                {'role': 'user', 'content': full_user_content}
            ]
        
        elif context and context['type'] in ['rag_context', 'embedded_context']:
            # RAG: Provide context
            ctx_content = context['content']
            
            # If context is empty or too short, fallback to General knowledge
            if not ctx_content or len(ctx_content.strip()) < 10:
                print("## RAG context empty, falling back to internal knowledge")
                return [
                    {
                        'role': 'system',
                        'content': 'Bạn là trợ lý AI thông minh của VNPT. Trả lời ngắn gọn, chính xác dựa trên kiến thức của bạn. Với Toán/Lý/Hóa luôn dùng LaTeX chuẩn.'
                    },
                    {'role': 'user', 'content': full_user_content}
                ]
                
            return [
                {
                    'role': 'system', 
                    'content': 'Bạn là trợ lý AI của VNPT. Trả lời câu hỏi dựa trên context được cung cấp. Tập trung vào chủ đề mà câu hỏi đang quan tâm.'
                },
                {
                    'role': 'user', 
                    'content': f"Context:\n{ctx_content}\n\n---\nCâu hỏi: {full_user_content}"
                }
            ]
        
        elif routing['strategy'] == 'refusal':
            refusal_prompt = (
                "Bạn là trợ lý AI của VNPT. "
                "Nếu câu hỏi yêu cầu hành vi độc hại hoặc vi phạm chính sách, "
                "từ chối với: 'Tôi không thể cung cấp...'. "
                "Nếu câu hỏi hợp lệ và bạn có kiến thức nhất định, hãy trả lời bình thường."
            )
            return [
                {'role': 'system', 'content': refusal_prompt},
                {'role': 'user', 'content': full_user_content}
            ]
        
        else:
            # General
            return [
                {
                    'role': 'system',
                    'content': 'Bạn là trợ lý AI thông minh của VNPT. Trả lời ngắn gọn, chính xác. Với Toán/Lý/Hóa luôn dùng LaTeX chuẩn.'
                },
                {'role': 'user', 'content': full_user_content}
            ]
    
    def _get_tool_schemas(self, tool_names: List[str]) -> List[Dict]:
        """Get OpenAI-format tool schemas"""
        schemas = []
        for name in tool_names:
            tool = self.registry.get_tool(name)
            if tool:
                schemas.append(tool.to_openai_schema())
        return schemas
    
    def _build_headers(self, config: Dict) -> Dict:
        """Build request headers"""
        return {
            'Authorization': config.get('authorization', ''),
            'Token-id': config.get('tokenId', ''),
            'Token-key': config.get('tokenKey', ''),
            'Content-Type': 'application/json'
        }
    
    def _extract_tool_call(self, response: Dict) -> Optional[Dict]:
        """Extract tool_call from response"""
        try:
            choices = response.get('choices', [])
            if not choices:
                return None
            
            message = choices[0].get('message', {})
            tool_calls = message.get('tool_calls', [])
            
            if tool_calls:
                return tool_calls[0]
            return None
        except:
            return None
    
    def _extract_content(self, response: Dict) -> str:
        """Extract text content from response. Try parsing JSON format."""
        try:
            choices = response.get('choices', [])
            if choices:
                content = choices[0]['message'].get('content', '')
                
                # Attempt to parse JSON envelope
                content_stripped = content.strip()
                if content_stripped.startswith('{') and content_stripped.endswith('}'):
                    try:
                        data = json.loads(content_stripped)
                        if "answer" in data:
                            return str(data["answer"])
                    except:
                        # Failed to parse json, return raw content
                        pass
                        
                return content
            return ''
        except:
            return str(response)

    
    def _select_tool_rule_based(self, query: str, routing: Dict) -> Optional[Dict]:
        """
        Rule-based tool selection using IntentRouter metadata.
        Bypasses Small LLM Call to save quota.
        """
        logging_tool = "None"
        tool_call = None
        
        # 1. Math/Logic -> solve_math_problem
        if 'solve_math_problem' in routing.get('tools', []):
            logging_tool = "solve_math_problem"
            tool_call = {
                'id': 'call_rule_based_math',
                'type': 'function',
                'function': {
                    'name': 'solve_math_problem',
                    'arguments': json.dumps({
                        'problem_statement': query,
                        'given_options': None # Can be parsed if needed, but tool handles it
                    })
                }
            }
            
        # 2. RAG -> search_knowledge_base
        elif 'search_knowledge_base' in routing.get('tools', []):
            logging_tool = "search_knowledge_base"
            tool_call = {
                'id': 'call_rule_based_rag',
                'type': 'function',
                'function': {
                    'name': 'search_knowledge_base',
                    'arguments': json.dumps({
                        'query': query,
                        'top_k': routing['metadata'].get('top_k', 5),
                        'min_score': routing['metadata'].get('min_score', 0.5)
                    })
                }
            }
            
        # 3. Embedded -> use_embedded_context
        elif 'use_embedded_context' in routing.get('tools', []):
            logging_tool = "use_embedded_context"
            tool_call = {
                'id': 'call_rule_based_embed',
                'type': 'function',
                'function': {
                    'name': 'use_embedded_context',
                    'arguments': json.dumps({
                        'full_text': query
                    })
                }
            }

        print(f"🤖 Rule-Based Tool Selection: {logging_tool}")
        return tool_call

# RateLimiter moved to src/functional/rate_limiter.py



    def _select_tool_rule_based(self, query: str, routing: Dict) -> Optional[Dict]:
        """
        Rule-based tool selection using IntentRouter metadata.
        Bypasses Small LLM Call to save quota.
        """
        logging_tool = "None"
        tool_call = None
        
        # 1. Math/Logic -> solve_math_problem
        if 'solve_math_problem' in routing.get('tools', []):
            logging_tool = "solve_math_problem"
            tool_call = {
                'id': 'call_rule_based_math',
                'type': 'function',
                'function': {
                    'name': 'solve_math_problem',
                    'arguments': json.dumps({
                        'problem_statement': query,
                        'given_options': None # Can be parsed if needed, but tool handles it
                    })
                }
            }
            
        # 2. RAG -> search_knowledge_base
        elif 'search_knowledge_base' in routing.get('tools', []):
            logging_tool = "search_knowledge_base"
            tool_call = {
                'id': 'call_rule_based_rag',
                'type': 'function',
                'function': {
                    'name': 'search_knowledge_base',
                    'arguments': json.dumps({
                        'query': query,
                        'top_k': routing['metadata'].get('top_k', 3),
                        'min_score': routing['metadata'].get('min_score', 0.5)
                    })
                }
            }
            
        # 3. Embedded -> use_embedded_context
        elif 'use_embedded_context' in routing.get('tools', []):
            logging_tool = "use_embedded_context"
            tool_call = {
                'id': 'call_rule_based_embed',
                'type': 'function',
                'function': {
                    'name': 'use_embedded_context',
                    'arguments': json.dumps({
                        'full_text': query
                    })
                }
            }

        print(f"🤖 Rule-Based Tool Selection: {logging_tool}")
        return tool_call


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VNPT AI Inference Runner")
    parser.add_argument("--data", default="dataset/test.json", help="Path to input dataset")
    parser.add_argument("--model-path", default="./models/intent/complex_dual_task", help="Intent model path")
    args = parser.parse_args()

    print(f"VNPT AI QA SYSTEM - INFERENCE MODE")
    print(f"Dataset: {args.data}")

    # Load dataset
    if not os.path.exists(args.data):
        print(f"[WARN] File not found: {args.data}")
        # Fallback search for private_test.json (standard submit environment)
        potential_paths = [
            "/code/private_test.json", 
            "private_test.json", 
            "dataset/private_test.json",
        ]
        found_path = None
        for p in potential_paths:
            if os.path.exists(p):
                found_path = p
                print(f"[INFO] Found dataset at fallback path: {p}")
                args.data = p
                break
        
        if not found_path:
            print(f"[ERR] Could not find dataset in {args.data} or fallback paths.")
            sys.exit(1)

    with open(args.data, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    # Initialize Engine
    try:
        qa_system = VNPTAI_QA(
            intent_model_path=args.model_path,
            enable_guardrails=True
        )
        
        # Run Scheduled Processing
        qa_system.inference(dataset)
        
        print("\n[INFO] Inference completed successfully.")
        
    except KeyboardInterrupt:
        print("\n [INFO] Interrupted by user.")
    except Exception as e:
        print(f"\n [ERR] Execution Error: {e}")
        import traceback
        traceback.print_exc()
                

