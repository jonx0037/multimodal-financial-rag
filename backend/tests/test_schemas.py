"""Tests for explainability Pydantic schemas."""

from app.models.schemas import (
    PipelineStage,
    QueryTermContribution,
    ResultExplanation,
    RetrievalExplainRequest,
    RetrievalExplainResponse,
    SentimentExplainRequest,
    SentimentExplainResponse,
    ShapToken,
)


def test_sentiment_explain_request_valid():
    req = SentimentExplainRequest(text="Apple reported record revenue")
    assert req.text == "Apple reported record revenue"


def test_sentiment_explain_response_shape():
    resp = SentimentExplainResponse(
        label="positive",
        confidence=0.94,
        probabilities={"positive": 0.94, "negative": 0.03, "neutral": 0.03},
        shap_values=[ShapToken(token="record", value=0.18)],
        base_value=0.33,
    )
    assert resp.label == "positive"
    assert len(resp.shap_values) == 1
    assert resp.shap_values[0].token == "record"


def test_retrieval_explain_request_valid():
    req = RetrievalExplainRequest(
        query="earnings growth",
        result_ids=["abc123"],
    )
    assert req.query == "earnings growth"
    assert len(req.result_ids) == 1


def test_retrieval_explain_response_shape():
    resp = RetrievalExplainResponse(
        results=[
            ResultExplanation(
                id="abc123",
                score=0.87,
                query_terms_contribution=[
                    QueryTermContribution(term="earnings", weight=0.42),
                ],
                modality="text",
                similarity_method="cosine on 3072-dim full vector",
            )
        ]
    )
    assert resp.results[0].id == "abc123"
    assert resp.results[0].query_terms_contribution[0].term == "earnings"


def test_pipeline_stage_shape():
    stage = PipelineStage(
        step=1,
        name="Embed Query",
        description="Your query is embedded into a vector using Gemini Embedding 2.",
        details={"model": "gemini-embedding-2-preview", "dimensions": 3072},
    )
    assert stage.step == 1
    assert stage.details["dimensions"] == 3072
