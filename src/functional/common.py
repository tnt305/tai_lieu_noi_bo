import re
from typing import List
import json

def clean_math_text(text: str) -> str:
    """
    Normalize math text to improve matching.
    Fixes common LaTeX typos like ' rac' -> '\\frac'.
    """
    if not text:
        return ""
        
    s = text.strip()
    
    # Fix common typo: ' rac' -> '\\frac'
    s = s.replace(' rac', '\\frac')
    s = s.replace('rac{', '\\frac{')
    
    # Remove whitespace for comparison
    s = "".join(s.split())
    
    return s

def fuzzy_math_match(answer: str, choices: List[str]) -> int:
    """
    Try to find the choice that contains the answer or strongly overlaps.
    Returns index of best match, or -1 if no good match.
    """
    clean_ans = clean_math_text(answer)
    
    # 1. Exact substring match (if answer is part of a choice)
    for i, choice in enumerate(choices):
        clean_choice = clean_math_text(choice)
        if clean_ans in clean_choice or clean_choice in clean_ans:
            len_ratio = len(clean_ans) / max(len(clean_choice), 1)
            if len_ratio > 0.3: 
                return i
                
    # 2. Token overlap (for jumbled symbols)
    def tokenize(t):
        return set(re.findall(r'[a-zA-Z0-9\+\-\*\\/\{\}\(\)\.\,]+', t))
        
    ans_tokens = tokenize(clean_ans)
    if not ans_tokens:
        return -1
        
    best_iou = 0.0
    best_idx = -1
    
    for i, choice in enumerate(choices):
        clean_choice = clean_math_text(choice)
        choice_tokens = tokenize(clean_choice)
        if not choice_tokens:
            continue
            
        intersection = ans_tokens.intersection(choice_tokens)
        union = ans_tokens.union(choice_tokens)
        iou = len(intersection) / len(union)
        
        if iou > best_iou:
            best_iou = iou
            best_idx = i
            
    if best_iou > 0.4:
        return best_idx
        
    return -1


def normalize_answer_to_letter(answer: str, choices: list = None) -> str:
    """
    Normalize predicted answer to choice letter (A, B, C, D...).
    
    Handles multiple formats:
    - JSON: {"answer": "X"}
    - Markdown code blocks: ```json ... ```
    - Plain letters: A, B, C...
    - Full choice text matching
    
    Args:
        answer: Raw answer string from LLM
        choices: List of choice texts to match against
        
    Returns:
        Normalized uppercase letter (A, B, C, D...) or original answer if no match
    """
    if not answer:
        return ""
    
    answer = answer.strip()
    clean_ans = answer
    
    # Try to extract from JSON format: {"answer": "..."}
    try:
        temp = answer
        if temp.startswith("```json"):
            temp = temp[7:]
        if temp.startswith("```"):
            temp = temp[3:]
        if temp.endswith("```"):
            temp = temp[:-3]
        temp = temp.strip()
        
        data = json.loads(temp)
        if isinstance(data, dict) and "answer" in data:
            clean_ans = str(data["answer"]).strip()
    except:
        pass
    
    # Try regex for {"answer": "..."} pattern
    match = re.search(r'\{\s*["\']?answer["\']?\s*:\s*["\']?([^"\'}\n]+)["\']?\s*\}', answer, re.IGNORECASE)
    if match:
        clean_ans = match.group(1).strip()

    # Map text answer back to choice letter if choices provided
    if choices:
        # Check if it's already a single letter (A, B, C, D...)
        # Allow A or A.
        match_letter = re.match(r'^([A-Z])\.?$', clean_ans, re.IGNORECASE)
        if match_letter:
            return match_letter.group(1).upper()
        
        # Check if it matches content of a choice
        for idx, choice in enumerate(choices):
            if str(choice).strip().lower() == clean_ans.strip().lower():
                return chr(65 + idx)  # A, B, C, D...

    return clean_ans
