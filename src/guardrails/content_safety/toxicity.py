"""
Toxicity Scanner - Phát hiện ngôn từ độc hại (Vietnamese support)

Sử dụng:
- Rule-based: Vietnamese toxic keywords
- Model-based: PhoBERT (optional, requires transformers)
"""
import re
import os
import numpy as np
from typing import Tuple, List, Set
import onnxruntime as ort
from transformers import AutoTokenizer
from ..base import Scanner


class ToxicityScanner(Scanner):
    _session_cache = {}
    _tokenizer_cache = {}

    def __init__(
        self,
        model_path="models/guardrails/toxicity/model.onnx",
        pretrained_name="models/guardrails/toxicity",
        max_length=512,
        use_gpu=False
    ):
        if os.path.isdir(model_path):
            model_path = os.path.join(model_path, "model.onnx")

        self.LABEL2ID = {"Positive": 0, "Toxic/Harm": 1}
        self.ID2LABEL = {0: "Positive", 1: "Toxic/Harm"}
        self.max_length = max_length

        # tokenizer
        if pretrained_name in self._tokenizer_cache:
            self.tokenizer = self._tokenizer_cache[pretrained_name]
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(pretrained_name)
            self._tokenizer_cache[pretrained_name] = self.tokenizer

        # onnx session
        providers = ["CUDAExecutionProvider"] if use_gpu else ["CPUExecutionProvider"]
        cache_key = (model_path, use_gpu)

        if cache_key in self._session_cache:
            self.session = self._session_cache[cache_key]
        else:
            self.session = ort.InferenceSession(model_path, providers=providers)
            self._session_cache[cache_key] = self.session

        self.input_names = [i.name for i in self.session.get_inputs()]
        self.output_name = self.session.get_outputs()[0].name

    @staticmethod
    def softmax(x):
        e = np.exp(x - np.max(x))
        return e / e.sum(axis=-1, keepdims=True)

    def scan(self, text: str):
        encoded = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="np"
        )

        ort_inputs = {
            "input_ids": encoded["input_ids"],
            "attention_mask": encoded["attention_mask"]
        }

        logits = self.session.run(
            [self.output_name],
            ort_inputs
        )[0]                     # [1, 2]

        probs = self.softmax(logits)[0]  # [2]
        pred_id = int(np.argmax(probs))

        return {
            "task": "toxicity",
            "prediction": self.ID2LABEL[pred_id],
            "confidence": {
                "Positive": float(probs[0]),
                "Toxic/Harm": float(probs[1]),
            },
            "is_toxic": pred_id == 1
        }
# Example usage
# model = ToxicityScanner(
#     model_path="/kaggle/working/Viguardrail-toxicity/model.onnx",
#     pretrained_name="unitary/unbiased-toxic-roberta",
#     multi_label=False
# )

# print(model.predict("You are stupid"))