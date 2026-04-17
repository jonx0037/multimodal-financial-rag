"""
Explainability service: SHAP-based sentiment explanation and retrieval explanation.
Uses the SHAP Partition explainer with FinBERT for token-level attributions.
"""

import logging

import numpy as np
import shap
import torch

from app.services.sentiment import SentimentService

logger = logging.getLogger(__name__)


class ExplainabilityService:
    def __init__(self, sentiment_service: SentimentService):
        self.sentiment_service = sentiment_service

        # Build a SHAP-compatible prediction function
        def predict_fn(texts: list[str]) -> np.ndarray:
            results = []
            for text in texts:
                inputs = sentiment_service.tokenizer(
                    text, return_tensors="pt", truncation=True, max_length=512
                )
                with torch.no_grad():
                    outputs = sentiment_service.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).squeeze().numpy()
                results.append(probs)
            return np.array(results)

        self.explainer = shap.Explainer(
            predict_fn,
            sentiment_service.tokenizer,
            output_names=["positive", "negative", "neutral"],
        )
        logger.info("SHAP explainer initialized with FinBERT")

    def explain_sentiment(self, text: str) -> dict:
        """
        Compute SHAP token attributions for sentiment prediction.

        Returns:
            {
                "label": str,
                "confidence": float,
                "probabilities": dict,
                "shap_values": [{"token": str, "value": float}, ...],
                "base_value": float,
            }
        """
        if not text.strip():
            raise ValueError("Input text must not be empty")

        # Get the prediction first
        prediction = self.sentiment_service.predict(text)
        label = prediction["label"]
        label_idx = ["positive", "negative", "neutral"].index(label)

        # Compute SHAP values
        shap_values = self.explainer([text])

        # Extract token-level values for the predicted class
        tokens = shap_values.data[0]
        values = shap_values.values[0][:, label_idx]
        base_value = float(shap_values.base_values[0][label_idx])

        shap_tokens = [
            {"token": str(tok), "value": round(float(val), 4)}
            for tok, val in zip(tokens, values)
            if str(tok).strip()  # Skip empty tokens
        ]

        return {
            "label": prediction["label"],
            "confidence": prediction["confidence"],
            "probabilities": prediction["probabilities"],
            "shap_values": shap_tokens,
            "base_value": round(base_value, 4),
        }

    def explain_retrieval_result(
        self,
        query_terms: list[str],
        query_vector: list[float],
        result_vector: list[float],
        result_id: str,
        score: float,
        modality: str,
        use_compact: bool = False,
    ) -> dict:
        """
        Explain why a result matched the query using cosine similarity decomposition.
        Assigns contribution weight to each query term proportional to element-wise
        product of query and result vectors, normalized.

        Returns:
            {
                "id": str,
                "score": float,
                "query_terms_contribution": [{"term": str, "weight": float}, ...],
                "modality": str,
                "similarity_method": str,
            }
        """
        q = np.array(query_vector)
        r = np.array(result_vector)

        # Element-wise product captures directional alignment
        element_products = q * r
        total = np.sum(np.abs(element_products))

        # Split vector dimensions evenly among query terms for attribution
        n_terms = len(query_terms)
        dims = len(query_vector)
        chunk_size = dims // max(n_terms, 1)

        contributions = []
        for i, term in enumerate(query_terms):
            start = i * chunk_size
            end = start + chunk_size if i < n_terms - 1 else dims
            chunk_sum = np.sum(element_products[start:end])
            weight = float(chunk_sum / total) if total > 0 else 0.0
            contributions.append({"term": term, "weight": round(weight, 4)})

        dim_label = "768-dim compact" if use_compact else "3072-dim full"
        return {
            "id": result_id,
            "score": score,
            "query_terms_contribution": contributions,
            "modality": modality,
            "similarity_method": f"cosine on {dim_label} vector",
        }
