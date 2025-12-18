"""
VNPT AI Inference Logging Utility using Loguru
Provides structured logging for the inference pipeline with detailed tracking.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger
from datetime import datetime


class VNPTAI_Logger:
    """
    Structured logger for VNPT AI inference pipeline.
    Logs: thinking content, toxicity checks, intent, answers, and calling flows.
    """
    
    def __init__(self, log_file: str = "logs/inference.txt"):
        """
        Initialize the VNPT AI inference logger.
        
        Args:
            log_file: Path to the log file
        """
        self.log_file = log_file
        
        # Ensure logs directory exists
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add file logger with custom format
        logger.add(
            log_file,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[qid]}</cyan> | "
                "{message}"
            ),
            level="INFO",
            rotation="10 MB",  # Rotate when file reaches 10MB
            retention="7 days",  # Keep logs for 7 days
            compression="zip",  # Compress rotated logs
            enqueue=True  # Thread-safe
        )
        
        # Also add console output for immediate feedback
        logger.add(
            lambda msg: print(msg, end=""),
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[qid]}</cyan> | "
                "{message}"
            ),
            level="INFO",
            colorize=True
        )
        
        logger.bind(qid="SYSTEM").info(f"VNPT AI Inference Logger initialized: {log_file}")
    
    def log_question_start(self, qid: str, question: str, choices: List[str]):
        """Log the start of processing a question."""
        with logger.contextualize(qid=qid):
            logger.info("=" * 80)
            logger.info(f"## PROCESSING QUESTION: {qid}")
            logger.info(f"Question: {question}")
            logger.info(f"Choices ({len(choices)}): {choices[:2]}..." if len(choices) > 2 else f"Choices: {choices}")
    
    def log_toxicity_check(
        self, 
        qid: str, 
        is_toxic: bool, 
        toxicity_score: Optional[float] = None,
        refusal_prob: Optional[float] = None
    ):
        """Log toxicity and safety check results."""
        with logger.contextualize(qid=qid):
            tox_score_str = f"{toxicity_score:.3f}" if toxicity_score is not None else "N/A"
            refusal_str = f"{refusal_prob:.3f}" if refusal_prob is not None else "N/A"
            
            if is_toxic:
                logger.warning(
                    f"## TOXICITY DETECTED | "
                    f"Toxic: {is_toxic} | "
                    f"Score: {tox_score_str} | "
                    f"Refusal Prob: {refusal_str}"
                )
            else:
                logger.info(
                    f"## SAFETY CHECK PASSED | "
                    f"Refusal Prob: {refusal_str}"
                )
    
    def log_intent_routing(
        self, 
        qid: str, 
        category: str, 
        tools: List[str],
        probs: Optional[Dict[str, float]] = None
    ):
        """Log intent classification and routing decision."""
        with logger.contextualize(qid=qid):
            prob_str = ""
            if probs:
                top_3 = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
                prob_str = " | ".join([f"{k}: {v:.3f}" for k, v in top_3])
            
            logger.info(
                f"## INTENT ROUTING | "
                f"Category: {category} | "
                f"Tools: {tools} | "
                f"Probs: {prob_str if prob_str else 'N/A'}"
            )
    
    def log_thinking_content(self, qid: str, thinking: str, model: str = "Large"):
        """Log the LLM's thinking/reasoning content."""
        with logger.contextualize(qid=qid):
            # Truncate if too long for readability
            max_len = 500
            thinking_display = (
                thinking[:max_len] + "..." if len(thinking) > max_len else thinking
            )
            logger.info(
                f"## {model.upper()} LLM THINKING\n"
                f"{'─' * 60}\n"
                f"{thinking_display}\n"
                f"{'─' * 60}"
            )
    
    def log_calling_flow(
        self, 
        qid: str, 
        flow_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log the LLM calling flow/strategy.
        
        Args:
            qid: Question ID
            flow_type: Type of flow (e.g., "RAG_DIRECT", "THINK_THEN_ANSWER", "VOTING_3LLM")
            details: Additional details about the flow
        """
        with logger.contextualize(qid=qid):
            details_str = ""
            if details:
                details_str = " | " + " | ".join([f"{k}: {v}" for k, v in details.items()])
            
            logger.info(f"## CALLING FLOW: {flow_type}{details_str}")
    
    def log_rag_context(
        self, 
        qid: str, 
        context_type: str,
        score: Optional[float] = None,
        snippet: Optional[str] = None
    ):
        """Log RAG/context retrieval information."""
        with logger.contextualize(qid=qid):
            snippet_display = ""
            if snippet:
                max_len = 200
                snippet_display = f"\n   Preview: {snippet[:max_len]}..." if len(snippet) > max_len else f"\n   Preview: {snippet}"
            
            score_str = f"{score:.3f}" if score is not None else "N/A"
            logger.info(
                f"## CONTEXT RETRIEVAL | "
                f"Type: {context_type} | "
                f"Score: {score_str}"
                f"{snippet_display}"
            )
    
    def log_final_answer(
        self, 
        qid: str, 
        raw_answer: str,
        verified_answer: str,
        confidence: Optional[float] = None,
        duration: Optional[float] = None
    ):
        """Log the final answer and verification results."""
        with logger.contextualize(qid=qid):
            conf_str = f" | Confidence: {confidence:.3f}" if confidence is not None else ""
            time_str = f" | Time: {duration:.2f}s" if duration is not None else ""
            
            logger.info(
                f"## FINAL ANSWER | "
                f"Raw: '{raw_answer}' -> Verified: '{verified_answer}'"
                f"{conf_str}{time_str}"
            )
    
    def log_error(self, qid: str, error: Exception, context: str = ""):
        """Log errors during processing."""
        with logger.contextualize(qid=qid):
            context_str = f" ({context})" if context else ""
            logger.error(f"## ERROR{context_str}: {type(error).__name__}: {str(error)}")
    
    def log_quota_exhausted(self, qid: str, model_type: str, wait_minutes: float):
        """Log quota exhaustion event."""
        with logger.contextualize(qid=qid):
            logger.warning(
                f"## QUOTA EXHAUSTED | "
                f"Model: {model_type} | "
                f"Wait: {wait_minutes:.1f} minutes"
            )
    
    def log_voting_results(
        self, 
        qid: str, 
        votes: List[str],
        final_vote: str,
        temperature: float
    ):
        """Log voting results from multiple LLM calls."""
        with logger.contextualize(qid=qid):
            from collections import Counter
            vote_counts = Counter(votes)
            vote_str = ", ".join([f"{v}: {c}" for v, c in vote_counts.items()])
            
            logger.info(
                f"## VOTING RESULTS | "
                f"Votes: [{', '.join(votes)}] | "
                f"Distribution: {{{vote_str}}} | "
                f"Final: {final_vote} | "
                f"Temp: {temperature}"
            )
    
    def log_question_complete(self, qid: str):
        """Log completion of question processing."""
        with logger.contextualize(qid=qid):
            logger.info("COMPLETED")
            logger.info("=" * 80 + "\n")


# Global logger instance
_GLOBAL_VNPTAI_LOGGER: Optional[VNPTAI_Logger] = None


def get_inference_logger(log_file: str = "logs/inference.txt") -> VNPTAI_Logger:
    """
    Get or create the global VNPT AI inference logger instance.
    
    Args:
        log_file: Path to log file (only used on first call)
        
    Returns:
        VNPTAI_Logger instance
    """
    global _GLOBAL_VNPTAI_LOGGER
    
    if _GLOBAL_VNPTAI_LOGGER is None:
        _GLOBAL_VNPTAI_LOGGER = VNPTAI_Logger(log_file)
    
    return _GLOBAL_VNPTAI_LOGGER
