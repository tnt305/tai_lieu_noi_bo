
import json
import os
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

import numpy as np
import torch
from tqdm import tqdm
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch.optim import AdamW

from transformers import AutoModel, AutoTokenizer
from huggingface_hub import PyTorchModelHubMixin
import onnxruntime as ort

from src.rag.intention.base import Extractor

# ========================== Model ==========================
class MeanPooling(nn.Module):
    """Mean pooling layer for sentence embeddings"""
    
    def __init__(self):
        super().__init__()
    
    def forward(
        self, 
        last_hidden_state: torch.Tensor, 
        attention_mask: torch.Tensor
    ) -> torch.Tensor:
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, dim=1)
        sum_mask = input_mask_expanded.sum(dim=1)
        sum_mask = torch.clamp(sum_mask, min=1e-9)
        return sum_embeddings / sum_mask


class RegressionHead(nn.Module):
    """Regression head for continuous value prediction"""
    
    def __init__(self, input_size: int, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        self.dense = nn.Linear(input_size, input_size // 2)
        self.activation = nn.GELU()
        self.output = nn.Linear(input_size // 2, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.dropout(x)
        x = self.dense(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.output(x)
        x = self.sigmoid(x)
        return x.squeeze(-1)


class ClassificationHead(nn.Module):
    """Classification head for category prediction"""
    
    def __init__(self, input_size: int, num_classes: int, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        self.dense = nn.Linear(input_size, input_size // 2)
        self.activation = nn.GELU()
        self.output = nn.Linear(input_size // 2, num_classes)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.dropout(x)
        x = self.dense(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.output(x)
        return x

class VietnameseComplexityClassifier(nn.Module, PyTorchModelHubMixin):
    """
    Vietnamese Complexity Classifier - Multi-task Model
    
    Tasks:
      - Regression: reasoning, contextual_knowledge, domain_knowledge, constraints
      - Classification: category (5 classes)
    """
    
    def __init__(
        self, 
        backbone_name: str = "5CD-AI/Vietnamese-Sentiment-visobert",
        target_names: List[str] = None,
        category_labels: List[str] = None,
        complexity_weights: Dict[str, float] = None,
        dropout: float = 0.1
    ):
        super().__init__()
        
        # Store config for PyTorchModelHubMixin
        self.backbone_name = backbone_name
        
        self.backbone = AutoModel.from_pretrained(backbone_name)
        self.hidden_size = self.backbone.config.hidden_size
        
        # Regression config
        self.target_names = target_names or [
            "reasoning", "contextual_knowledge", "domain_knowledge", "constraints"
        ]
        
        self.complexity_weights = complexity_weights or {
            "reasoning": 0.30,
            "contextual_knowledge": 0.20,
            "domain_knowledge": 0.30,
            "constraints": 0.20
        }
        
        # Classification config
        self.category_labels = category_labels or [
            "General", "LongContext", "NeutralPOV", "Correctness", "Refusal", "MathLogic"
        ]
        self.num_labels = len(self.category_labels)
        self.id2label = {i: label for i, label in enumerate(self.category_labels)}
        self.label2id = {label: i for i, label in enumerate(self.category_labels)}
        
        self.pool = MeanPooling()
        
        # Regression heads (4 heads)
        self.regression_heads = nn.ModuleDict({
            name: RegressionHead(self.hidden_size, dropout)
            for name in self.target_names
        })
        
        # Classification head (1 head for category)
        self.category_head = ClassificationHead(
            self.hidden_size, 
            self.num_labels, 
            dropout
        )
    
    def forward(
        self, 
        input_ids: torch.Tensor, 
        attention_mask: torch.Tensor,
        regression_labels: Optional[torch.Tensor] = None,
        category_label: Optional[torch.Tensor] = None,
        regression_loss_weight: float = 1.0,
        classification_loss_weight: float = 1.0
    ) -> Dict[str, torch.Tensor]:
        
        # Backbone forward
        outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = outputs.last_hidden_state
        pooled_output = self.pool(last_hidden_state, attention_mask)
        
        # ============ REGRESSION BRANCH ============
        regression_predictions = {}
        regression_logits_list = []
        
        for name in self.target_names:
            pred = self.regression_heads[name](pooled_output)
            regression_predictions[name] = pred
            regression_logits_list.append(pred)
        
        regression_logits = torch.stack(regression_logits_list, dim=1)
        
        # Complexity score
        complexity_score = sum(
            regression_predictions[name] * self.complexity_weights[name]
            for name in self.target_names
        )
        regression_predictions["complexity_score"] = complexity_score
        
        # ============ CLASSIFICATION BRANCH ============
        category_logits = self.category_head(pooled_output)
        category_probs = F.softmax(category_logits, dim=-1)
        category_pred = torch.argmax(category_probs, dim=-1)
        
        # ============ COMPUTE LOSS ============
        total_loss = None
        regression_loss = None
        classification_loss = None
        
        if regression_labels is not None:
            regression_loss = F.mse_loss(regression_logits, regression_labels)
        
        if category_label is not None:
            classification_loss = F.cross_entropy(category_logits, category_label)
        
        if regression_loss is not None and classification_loss is not None:
            total_loss = (
                regression_loss_weight * regression_loss + 
                classification_loss_weight * classification_loss
            )
        elif regression_loss is not None:
            total_loss = regression_loss
        elif classification_loss is not None:
            total_loss = classification_loss
        
        return {
            "loss": total_loss,
            "regression_loss": regression_loss,
            "classification_loss": classification_loss,
            "regression_logits": regression_logits,
            "regression_predictions": regression_predictions,
            "category_logits": category_logits,
            "category_probs": category_probs,
            "category_pred": category_pred
        }
    
    @torch.no_grad()
    def predict(
        self, 
        input_ids: torch.Tensor, 
        attention_mask: torch.Tensor
    ) -> Dict:
        """Inference method"""
        self.eval()
        outputs = self.forward(input_ids, attention_mask)
        
        # Convert category prediction to labels
        category_indices = outputs["category_pred"].cpu().tolist()
        category_labels_pred = [self.id2label[idx] for idx in category_indices]
        
        result = {
            **{k: v.cpu().tolist() for k, v in outputs["regression_predictions"].items()},
            "category": category_labels_pred,
            "category_probs": outputs["category_probs"].cpu().tolist()
        }
        return result


class VNPTAI_INTENT_CLASSIFIER_BASE(Extractor):
    """
    Base class for Vietnamese Intent Classifier
    ONNX-based Vietnamese Intent Classifier
    Optimized for CPU inference
    """
    
    _session_cache = {}
    _tokenizer_cache = {}
    
    def __init__(
        self,
        model_path: str = "./models/intent/complex_dual_task",
        tokenizer_path: str = None,
        use_gpu: bool = False,
        num_threads: int = 4
    ):
        """
        Initialize ONNX classifier
        
        Args:
            model_path: Path to ONNX model file or directory containing model.onnx
            tokenizer_path: Path to tokenizer (default: same as model_path parent)
            use_gpu: Whether to use GPU (requires onnxruntime-gpu)
            num_threads: Number of threads for inference (None = auto)
        """
        # Handle path
        if os.path.isdir(model_path):
            onnx_path = os.path.join(model_path, "model.onnx")
            config_path = os.path.join(model_path, "onnx_config.json")
            tokenizer_path = tokenizer_path or model_path
        else:
            onnx_path = model_path
            config_path = os.path.join(os.path.dirname(model_path), "onnx_config.json")
            tokenizer_path = tokenizer_path or os.path.dirname(model_path)
        
        # Load config
        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        self.target_names = self.config["target_names"]
        self.category_labels = self.config["category_labels"]
        self.complexity_weights = self.config["complexity_weights"]
        self.max_length = self.config.get("max_length", 256)
        self.id2label = {int(k): v for k, v in self.config["id2label"].items()}
        
        # Load tokenizer
        if tokenizer_path in self._tokenizer_cache:
            self.tokenizer = self._tokenizer_cache[tokenizer_path]
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
            self._tokenizer_cache[tokenizer_path] = self.tokenizer
        
        # Create ONNX session
        cache_key = (onnx_path, use_gpu, num_threads)
        
        if cache_key in self._session_cache:
            self.session = self._session_cache[cache_key]
        else:
            session_options = ort.SessionOptions()
            
            if num_threads is not None:
                session_options.intra_op_num_threads = num_threads
                session_options.inter_op_num_threads = num_threads
            
            # Enable optimizations
            session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            # Select providers
            if use_gpu:
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            else:
                providers = ["CPUExecutionProvider"]
            
            self.session = ort.InferenceSession(
                onnx_path,
                sess_options=session_options,
                providers=providers
            )
            self._session_cache[cache_key] = self.session
        
        # Get input/output names
        self.input_names = [inp.name for inp in self.session.get_inputs()]
        self.output_names = [out.name for out in self.session.get_outputs()]
        
        print(f"ONNX model loaded from {onnx_path}")
        print(f"Providers: {self.session.get_providers()}")
    
    def _tokenize(self, texts: Union[str, List[str]]) -> Dict[str, np.ndarray]:
        """Tokenize input texts"""
        if isinstance(texts, str):
            texts = [texts]
        
        encoded = self.tokenizer(
            texts,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="np"
        )
        
        return {
            "input_ids": encoded["input_ids"].astype(np.int64),
            "attention_mask": encoded["attention_mask"].astype(np.int64)
        }
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax"""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)
    
    def predict(self, texts: Union[str, List[str]]) -> Dict[str, List]:
        """
        Predict complexity scores and category
        
        Args:
            texts: Single text or list of texts
        
        Returns:
            Dictionary with predictions
        """
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]
        
        # Tokenize
        inputs = self._tokenize(texts)
        
        # Run inference
        outputs = self.session.run(
            self.output_names,
            {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"]
            }
        )
        
        regression_logits = outputs[0]  # (batch_size, 4)
        category_logits = outputs[1]    # (batch_size, num_categories)
        
        # Process regression outputs
        result = {}
        for i, name in enumerate(self.target_names):
            result[name] = regression_logits[:, i].tolist()
        
        # Compute complexity score
        complexity_scores = sum(
            np.array(result[name]) * self.complexity_weights[name]
            for name in self.target_names
        )
        result["complexity_score"] = complexity_scores.tolist()
        
        # Process category outputs
        category_probs = self._softmax(category_logits)
        category_indices = np.argmax(category_probs, axis=-1)
        
        result["category"] = [self.id2label[idx] for idx in category_indices]
        result["category_probs"] = category_probs.tolist()
        
        return result
    
    def scan(self, text: str) -> Dict:
        """
        Detect intent for a single text with formatted output
        
        Args:
            text: Input text
        
        Returns:
            Formatted prediction dictionary
        """
        result = self.predict(text)
        
        return {
            "text": text,
            "category": result["category"][0],
            "category_probs": {
                label: prob 
                for label, prob in zip(self.category_labels, result["category_probs"][0])
            },
            "complexity": {
                "reasoning": result["reasoning"][0],
                "contextual_knowledge": result["contextual_knowledge"][0],
                "domain_knowledge": result["domain_knowledge"][0],
                "constraints": result["constraints"][0],
                "score": result["complexity_score"][0]
            }
        }
    
    def extract(self, prompt: str) -> Tuple[str, bool, float]:
        """
        Implementation of Extractor protocol
        
        Returns:
            - prompt: Original prompt (unchanged)
            - is_valid: True (always valid for intent classification)
            - risk_score: Complexity score as risk indicator
        """
        result = self.scan(prompt)
        complexity_score = result["complexity"]["score"]
        return prompt, True, complexity_score