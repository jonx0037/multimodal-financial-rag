"""Tests for ExplainabilityService -- SHAP-based sentiment explanation."""

import pytest

from app.services.explainability import ExplainabilityService
from app.services.sentiment import SentimentService


@pytest.fixture(scope="module")
def sentiment_service():
    return SentimentService()


@pytest.fixture(scope="module")
def explainability_service(sentiment_service):
    return ExplainabilityService(sentiment_service)


def test_explain_sentiment_returns_shap_tokens(explainability_service):
    result = explainability_service.explain_sentiment(
        "Apple reported record Q4 revenue growth"
    )
    assert "shap_values" in result
    assert len(result["shap_values"]) > 0
    assert "token" in result["shap_values"][0]
    assert "value" in result["shap_values"][0]


def test_explain_sentiment_includes_prediction(explainability_service):
    result = explainability_service.explain_sentiment(
        "Revenue surged 25% beating all expectations"
    )
    assert result["label"] in ("positive", "negative", "neutral")
    assert 0.0 <= result["confidence"] <= 1.0
    assert "probabilities" in result
    assert "base_value" in result


def test_explain_sentiment_base_value_near_third(explainability_service):
    result = explainability_service.explain_sentiment("Market conditions are uncertain")
    # Base value for 3-class should be a valid probability (not 0 or 1 exactly)
    assert 0.0 < result["base_value"] < 1.0


def test_explain_sentiment_empty_raises(explainability_service):
    with pytest.raises(ValueError, match="empty"):
        explainability_service.explain_sentiment("")


def test_explain_retrieval_computes_cosine_similarity():
    """Test retrieval explanation computes actual cosine similarity."""
    service = ExplainabilityService.__new__(ExplainabilityService)

    query_vector = [1.0, 0.0, 0.0, 0.0]
    result_vector = [1.0, 0.0, 0.0, 0.0]

    explanation = service.explain_retrieval_result(
        query_vector=query_vector,
        result_vector=result_vector,
        result_id="abc123",
        modality="text",
        use_compact=False,
    )
    assert explanation["id"] == "abc123"
    assert explanation["score"] == 1.0  # identical vectors = perfect similarity
    assert explanation["similarity_method"] == "cosine on 3072-dim full vector"


def test_explain_retrieval_with_term_vectors():
    """Test retrieval explanation with per-term cosine similarity."""
    service = ExplainabilityService.__new__(ExplainabilityService)

    result_vector = [0.5, 0.3, 0.8, 0.1]
    term_vectors = {
        "earnings": [0.9, 0.1, 0.0, 0.0],  # aligned on dim 0
        "growth": [0.0, 0.0, 0.9, 0.1],  # aligned on dim 2
    }

    explanation = service.explain_retrieval_result(
        query_vector=[0.5, 0.3, 0.8, 0.1],
        result_vector=result_vector,
        result_id="abc123",
        modality="text",
        term_vectors=term_vectors,
    )
    assert len(explanation["query_terms_contribution"]) == 2
    # "growth" should have higher weight (more aligned with result on dim 2)
    weights = {c["term"]: c["weight"] for c in explanation["query_terms_contribution"]}
    assert weights["growth"] > weights["earnings"]
