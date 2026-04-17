"""Tests for the SentimentService wrapping FinBERT."""

import pytest

from app.services.sentiment import SentimentService


@pytest.fixture(scope="module")
def sentiment_service():
    """Load FinBERT once for all tests in this module."""
    return SentimentService()


def test_predict_returns_label_and_confidence(sentiment_service):
    result = sentiment_service.predict("Apple reported record Q4 revenue growth")
    assert result["label"] in ("positive", "negative", "neutral")
    assert 0.0 <= result["confidence"] <= 1.0
    assert "probabilities" in result
    assert set(result["probabilities"].keys()) == {"positive", "negative", "neutral"}


def test_predict_positive_sentiment(sentiment_service):
    result = sentiment_service.predict("Revenue surged 25% beating all expectations")
    assert result["label"] == "positive"
    assert result["confidence"] > 0.5


def test_predict_negative_sentiment(sentiment_service):
    result = sentiment_service.predict("The company reported massive losses and declining revenue")
    assert result["label"] == "negative"
    assert result["confidence"] > 0.5


def test_predict_probabilities_sum_to_one(sentiment_service):
    result = sentiment_service.predict("Market conditions remain uncertain")
    probs = result["probabilities"]
    total = sum(probs.values())
    assert abs(total - 1.0) < 0.01


def test_predict_empty_string_raises(sentiment_service):
    with pytest.raises(ValueError, match="empty"):
        sentiment_service.predict("")
