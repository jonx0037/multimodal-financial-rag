"""
Explainability service: SHAP-based sentiment explanation and retrieval explanation.
Uses the SHAP Partition explainer with FinBERT for token-level attributions.
"""

import logging

import numpy as np

try:
    import shap
    import torch
except ImportError:
    shap = None  # type: ignore[assignment]
    torch = None  # type: ignore[assignment]

from app.services.sentiment import LABELS, SentimentService

logger = logging.getLogger(__name__)


class ExplainabilityService:
    def __init__(self, sentiment_service: SentimentService):
        self.sentiment_service = sentiment_service

        # SHAP passes inputs as numpy arrays; HuggingFace tokenizer requires
        # a plain list[str], so we coerce before forwarding to the model.
        def predict_fn(texts) -> np.ndarray:
            texts_list = [str(t) for t in texts]
            inputs = sentiment_service.tokenizer(
                texts_list, return_tensors="pt", padding=True, truncation=True, max_length=512
            )
            with torch.no_grad():
                outputs = sentiment_service.model(**inputs)
            return torch.softmax(outputs.logits, dim=-1).cpu().numpy()

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
        label_idx = LABELS.index(label)

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

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def explain_retrieval_result(
        self,
        query_vector: list[float],
        result_vector: list[float],
        result_id: str,
        modality: str,
        term_vectors: dict[str, list[float]] | None = None,
        use_compact: bool = False,
    ) -> dict:
        """
        Explain why a result matched the query.

        Computes the actual cosine similarity score between query and result vectors.
        If per-term vectors are provided (each query term embedded individually),
        computes per-term cosine similarity against the result to show which terms
        contributed most to the match.

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

        score = self.cosine_similarity(q, r)

        contributions = []
        if term_vectors:
            # Compute per-term cosine similarity with result vector
            raw_sims = {}
            for term, vec in term_vectors.items():
                raw_sims[term] = max(0.0, self.cosine_similarity(np.array(vec), r))

            total = sum(raw_sims.values())
            for term, sim in raw_sims.items():
                weight = sim / total if total > 0 else 0.0
                contributions.append({"term": term, "weight": round(weight, 4)})

        dim_label = "768-dim compact" if use_compact else "3072-dim full"
        return {
            "id": result_id,
            "score": round(score, 4),
            "query_terms_contribution": contributions,
            "modality": modality,
            "similarity_method": f"cosine on {dim_label} vector",
        }
