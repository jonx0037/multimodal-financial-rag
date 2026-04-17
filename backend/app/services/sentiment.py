"""
Wraps ProsusAI/finbert for financial sentiment classification.
Model is loaded once at initialization. Inference is synchronous --
callers should use asyncio.to_thread() for async contexts.
"""

import logging

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

LABELS = ["positive", "negative", "neutral"]


class SentimentService:
    MODEL_NAME = "ProsusAI/finbert"

    def __init__(self):
        logger.info("Loading FinBERT model: %s", self.MODEL_NAME)
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
        self.model.eval()
        logger.info("FinBERT model loaded successfully")

    def predict(self, text: str) -> dict:
        """
        Run FinBERT on a text and return label, confidence, and per-class probabilities.

        Returns:
            {
                "label": "positive" | "negative" | "neutral",
                "confidence": float,
                "probabilities": {"positive": float, "negative": float, "neutral": float},
            }
        """
        if not text.strip():
            raise ValueError("Input text must not be empty")

        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = torch.softmax(outputs.logits, dim=-1).squeeze()
        confidence, predicted_idx = torch.max(probs, dim=-1)

        return {
            "label": LABELS[predicted_idx.item()],
            "confidence": round(confidence.item(), 4),
            "probabilities": {
                label: round(prob.item(), 4) for label, prob in zip(LABELS, probs)
            },
        }
