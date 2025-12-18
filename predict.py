
import sys
import os
import re
import time
import json
import io
import contextlib
import traceback
from typing import Dict, List, Any, Optional, Tuple
sys.path.append(os.getcwd())

import requests
from tqdm import tqdm

# Import project modules
from predict_base import VNPTAI_QA
from src.functional.constants import API_URL, API_URL_SMALL
from src.rag.correction import QuotaExhaustedException
from src.rag.prompts.math_program import (
    MATH_PROGRAM_SYSTEM,
    MATH_PROGRAM_USER_TEMPLATE,
    MATH_FALLBACK_JUDGE_SYSTEM
)
from src.functional.common import normalize_answer_to_letter


class HITMAN_VNPTAI(VNPTAI_QA):
    """
    Math/Science specialized solver using Rationale -> Program -> Execute Loop.
    Inherits from VNPTAI_QA to reuse tools, logging, and rate limiters.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("[INIT] MathSolver initialized with Rationale-Program Strategy")

    def _execute_python_code(self, code_str: str, timeout: int = 5) -> Tuple[bool, str]:
        """
        Execute generated Python code in a captured stdout environment.
        Returns: (success, output_or_error)
        """
        # Create a buffer to capture stdout
        buffer = io.StringIO()
        
        # Safe globals (basic math)
        safe_globals = {
            "math": __import__("math"),
            "__builtins__": __builtins__, # Needed for standard types, be careful in prod
        }
        safe_locals = {}
        
        try:
            # Capture stdout
            with contextlib.redirect_stdout(buffer):
                exec(code_str, safe_globals, safe_locals)
            
            output = buffer.getvalue().strip()
            return True, output
            
        except Exception as e:
            error_msg = traceback.format_exc()
            return False, f"Runtime Error: {e}\n{error_msg}"
        finally:
            buffer.close()

    def _generate_rationale_code(self, query: str, choices: List[str]) -> Tuple[str, str, str]:
        """
        Call Large LLM to generate Thinking and Python Code.
        Returns: (full_content, thinking, python_code)
        """
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        user_msg = MATH_PROGRAM_USER_TEMPLATE.format(question=query, choices_str=choices_str)
        
        headers = self._build_headers(self.large_llm_config)
        data = {
            'model': 'vnptai_hackathon_large',
            'messages': [ 
                {'role':'system', 'content': MATH_PROGRAM_SYSTEM}, 
                {'role':'user', 'content': user_msg} 
            ],
            'max_completion_tokens': 512, # Need enough space for code
            'temperature': 0.7,
            'top_p': 0.9
            # NO STOP TOKEN as per request: "bỏ stop tại </think>"
        }
        
        try:
            # Consume 1 Large Call
            # self.large_limiter.wait_if_needed(1) # Moved to caller to track time
            self.large_llm_calls += 1 
            
            resp = requests.post(API_URL, headers=headers, json=data, timeout=60)
            self._check_rate_limit(resp, "Large")
            
            if resp.status_code == 200:
                content = self._extract_content(resp.json())
                
                # Extract Thinking
                thinking = ""
                think_match = re.search(r'<think>(.*?)</think>', content, re.DOTALL | re.IGNORECASE)
                if think_match:
                    thinking = think_match.group(1).strip()
                
                # Extract Code
                code = ""
                code_match = re.search(r'```python(.*?)```', content, re.DOTALL | re.IGNORECASE)
                if code_match:
                    code = code_match.group(1).strip()
                else:
                    # Retry regex without python label
                    code_match = re.search(r'```(.*?)```', content, re.DOTALL | re.IGNORECASE)
                    if code_match:
                        code = code_match.group(1).strip()

                return content, thinking, code
                
            return "", "", ""
            
        except QuotaExhaustedException:
            raise
        except Exception as e:
            print(f"[ERR] Rationale-Code Gen Error: {e}")
            return "", "", ""

    def _select_final_answer_with_program(self, query: str, choices: List[str], thinking: str, code_output: str) -> str:
        """
        Small LLM selects the final choice based on logic + code result.
        """
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        
        sys_prompt = "Bạn là trợ lý tổng hợp kết quả. Dựa trên tính toán từ code, hãy chọn phương án đúng."
        
        user_msg = (
            f"Câu hỏi: {query}\nLựa chọn:\n{choices_str}\n\n"
            f"--- SUY LUẬN (Tóm tắt) ---\n{thinking[:1000]}...\n"
            f"--- KẾT QUẢ CHẠY CODE ---\n{code_output}\n"
            f"-------------------------\n"
            "Hãy so sánh kết quả chạy code với các lựa chọn và chốt đáp án JSON: {\"answer\": \"X\"}"
        )
        
        headers = self._build_headers(self.small_llm_config)
        data = {
            'model': 'vnptai_hackathon_small',
            'messages': [ {'role':'system', 'content': sys_prompt}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 64,
            'temperature': 0.1 # Strict
        }
        
        try:
            self.small_llm_calls += 1
            
            resp = requests.post(API_URL_SMALL, headers=headers, json=data, timeout=20)
            self._check_rate_limit(resp, "Small")
            if resp.status_code == 200:
                raw = self._extract_content(resp.json())
                return normalize_answer_to_letter(raw, choices)
            return "Error"
        except Exception as e:
            print(f"[ERR] Small Final Select Error: {e}")
            return "Error"

    def _fallback_judge_selection(self, query: str, choices: List[str], thinking: str) -> str:
        """
        Fallback: Use Small LLM as Judge to pick answer based on Thinking (No Code).
        """
        choices_str = "\n".join([f"{chr(65+i)}. {c}" for i, c in enumerate(choices or [])])
        
        user_msg = (
            f"Câu hỏi: {query}\nLựa chọn:\n{choices_str}\n\n"
            f"--- SUY LUẬN CỦA CHUYÊN GIA ---\n{thinking}\n"
            f"-------------------------------\n"
            "Dựa trên suy luận trên, hãy chọn đáp án đúng nhất. JSON: {\"answer\": \"X\"}"
        )
        
        headers = self._build_headers(self.small_llm_config)
        data = {
            'model': 'vnptai_hackathon_small',
            'messages': [ {'role':'system', 'content': MATH_FALLBACK_JUDGE_SYSTEM}, {'role':'user', 'content': user_msg} ],
            'max_completion_tokens': 64,
            'temperature': 0.2
        }
        
        try:
            self.small_llm_calls += 1
            
            resp = requests.post(API_URL_SMALL, headers=headers, json=data, timeout=20)
            if resp.status_code == 200:
                raw = self._extract_content(resp.json())
                return normalize_answer_to_letter(raw, choices)
            return "Error"
        except Exception:
            return "Error"

    def inference(self, dataset: List[Dict]) -> List[Dict]:
        """
        Override inference to inject Math Logic Loop.
        Other categories fall back to standard behavior (conceptually).
        Since we can't easily call super().inference() for just 'one item',
        we essentially rewrite the loop but delegate non-math items to standard flow logic.
        
        Actually, to keep it simple as requested ("Tạo file tương tự"), I will replicate the loop structure
        but modify the branch for Math.
        """
        all_results = []
        total_items = len(dataset)
        
        print(f"\n[INFO] Starting MathSolver Inference: {total_items} items")
        
        # Setup TQDM
        try:
             pbar = tqdm(total=total_items, desc="Processing")
        except TypeError:
             pbar = tqdm.tqdm(total=total_items, desc="Processing")
             
        idx = 0
        while idx < total_items:
            item = dataset[idx]
            qid = item.get('qid')
            pbar.set_description(f"Processing {qid}")
            query = item.get('question')
            choices = item.get('choices', [])
            
            self.logger.log_question_start(qid, query, choices)
            start_time = time.time()
            total_sleep = 0.0
            
            try:
                # 1. Router
                default_routing = {'tools': ['search_knowledge_base'], 'metadata': {}, 'category': 'General', 'probs': {}}
                routing = self.router.route(query) if hasattr(self, 'router') and self.router else default_routing
                category = routing.get('category', 'General')
                
                # Math Keywords Check (Force Math Mode for scientific topics)
                math_topics = ['MathLogic', 'Calculus', 'Statistics', 'Physics', 'Chemistry', 'Economics']
                is_math_mode = category in math_topics
                
                # Check keywords if category is ambiguous
                if not is_math_mode:
                    keywords = ['tính', 'giá trị', 'bao nhiêu', 'phương trình', 'hàm số', 'khối lượng', 'tốc độ']
                    if any(k in query.lower() for k in keywords) and 'đâu là' not in query.lower():
                        # Heuristic: looks like math
                        pass 

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
                    # Note: refusal_detector is inherited from VNPTAI_QA
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
                        
                final_answer = "Error"
                final_verified = "Error"

                # === BRANCH: MATH MODE ===
                if is_math_mode:
                    print(f"   [MATH-MODE] {qid} ({category}) -> Rationale-Program Flow")
                    self.logger.log_calling_flow(qid, "MATH_PROGRAM_EXEC", {"pipeline": "Rationale->Code->Exec->Select"})
                    
                    # Step 1: Generate Rationale + Code
                    print("   [1] Generating Rationale & Code...")
                    total_sleep += self.large_limiter.wait_if_needed(1)
                    full_content, thinking, code = self._generate_rationale_code(query, choices)
                    
                    # Log full content as requested
                    self.logger.log_thinking_content(qid, full_content, "Large_Rationale_Code")
                    
                    if code:
                        print(f"   [2] Executing Python Code... ({len(code)} chars)")
                        success, exec_output = self._execute_python_code(code)
                        print(f"      -> Output: {exec_output[:100]}...")
                        
                        if success:
                            # Step 3: Select Answer based on Exec Output
                            print("   [3] Selecting Final Answer...")
                            total_sleep += self.small_limiter.wait_if_needed(1)
                            final_answer = self._select_final_answer_with_program(query, choices, thinking, exec_output)
                            
                            # Validate if answer is valid letter (A-Z)
                            is_valid_letter = final_answer and len(final_answer) == 1 and 'A' <= final_answer <= 'K'
                            
                            if is_valid_letter:
                                self.logger.log_voting_results(qid, [exec_output], final_answer, 1.0)
                            else:
                                print(f"      [WARN] Program output '{exec_output}' -> '{final_answer}' (Invalid). Fallback to Judge.")
                                total_sleep += self.small_limiter.wait_if_needed(1)
                                final_answer = self._fallback_judge_selection(query, choices, thinking)
                        else:
                            # Exec Failed -> Fallback
                            print(f"      [FAIL] Runtime Error. Fallback to Judge.")
                            total_sleep += self.small_limiter.wait_if_needed(1)
                            final_answer = self._fallback_judge_selection(query, choices, thinking)
                    else:
                        print("      [FAIL] No Code generated. Fallback to Judge.")
                        total_sleep += self.small_limiter.wait_if_needed(1)
                        final_answer = self._fallback_judge_selection(query, choices, thinking)

                # === BRANCH: NORMAL FLOW (Copy from predict.py for other types) ===
                else:
                    # Reuse standard logic (Simplified call to avoid code dup if possible, otherwise embedded)
                    # Since we can't easily invoke "just the logic" of parent without refactoring parent, 
                    # we will use a simplified fallback: Just use Large Direct or standard flow.
                    # For this specific task, let's treat non-math items with standard "Think -> Small Answer" flow
                    
                    print(f"   [STD-MODE] {qid} ({category}) -> Standard Flow")
                    # Use RAG if needed (omitted for brevity unless requested to be full parity)
                    # Assuming we just want to process them reasonably well.
                    
                    self.logger.log_calling_flow(qid, "STANDARD_THINK", {})
                    # Large Think
                    print("   [THINK] Reasoning...")
                    total_sleep += self.large_limiter.wait_if_needed(1)
                    thinking_content, _ = self._call_large_think_only(query, None, choices) # Use parent method
                    self.logger.log_thinking_content(qid, thinking_content, "Large")
                    
                    # Small Answer
                    print("   [ANSWER] Generating...")
                    total_sleep += self.small_limiter.wait_if_needed(1)
                    final_answer = self._call_small_answer(query, None, choices, thinking_content)

                # Final Verify (Common)
                final_verified = self.verifier.verify(query, choices, final_answer, qid=qid)
                
                # Timing
                end_time = time.time()
                duration = round(end_time - start_time - total_sleep, 2)
                
                self.logger.log_final_answer(qid, final_answer, final_verified, duration=duration)
                self.logger.log_question_complete(qid)
                print(f"   [OK] Answer: {final_verified} (Time: {duration}s)")
                
                res = {"qid": qid, "answer": final_verified, "time": duration}
                all_results.append(res)
                self._save_sample_result(res)
                
                idx += 1
                pbar.update(1)

            except QuotaExhaustedException as e:
                self.logger.log_quota_exhausted(qid, e.model_type, e.wait_minutes)
                print(f"\n[WAIT] RATE LIMIT ({e}). Sleeping 1 hour before retrying item {qid}...")
                for _ in tqdm(range(60), desc="Quota Reset Wait (mins)"):
                    time.sleep(60)  # Wait 60 minutes total (1 hour)
                    total_sleep += 60.0 # Just for tracking, though resetting on retry clears this
                print("[RESUME] Resuming same item...")
                # Retry same item
                
            except Exception as e:
                print(f"[ERR] {e}")
                idx += 1
                pbar.update(1)
        
        pbar.close()
        return all_results

if __name__ == "__main__":
    # Robust Dataset Loading Logic
    candidate_paths = [
        "/code/private_test.json",           # 1. Docker/Scoring Path (Priority)
        "private_test.json",                 # 2. Relative Path (Docker WORKDIR /code or Root)
        "dataset/private_test.json",         # 3. Local Private Test
        "dataset/test.json",                 
        # "dataset/public_test.json",  
    ]
    
    data = None
    loaded_path = ""
    
    for path in candidate_paths:
        if os.path.exists(path):
            try:
                print(f"[LOAD] Found dataset at: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                loaded_path = path
                break
            except Exception as e:
                print(f"[WARN] Failed to read {path}: {e}")
    
    if data:
        print(f"[INFO] Starting Inference on {len(data)} items from {loaded_path}...")
        solver = HITMAN_VNPTAI(enable_guardrails=True)
        results = solver.inference(data)
    else:
        print("[ERR] CRITICAL: No dataset found in candidate paths!")
        print(f"      Checked: {candidate_paths}")
        sys.exit(1)
