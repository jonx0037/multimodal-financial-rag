"""Tests for the explain API endpoints."""

import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_sentiment_service():
    service = MagicMock()
    return service


@pytest.fixture
def mock_explainability_service():
    service = MagicMock()
    service.explain_sentiment = MagicMock(return_value={
        "label": "positive",
        "confidence": 0.94,
        "probabilities": {"positive": 0.94, "negative": 0.03, "neutral": 0.03},
        "shap_values": [
            {"token": "record", "value": 0.18},
            {"token": "revenue", "value": 0.12},
        ],
        "base_value": 0.33,
    })
    service.explain_retrieval_result = MagicMock(return_value={
        "id": "abc123",
        "score": 0.87,
        "query_terms_contribution": [
            {"term": "earnings", "weight": 0.42},
        ],
        "modality": "text",
        "similarity_method": "cosine on 3072-dim full vector",
    })
    return service


@pytest.fixture
async def explain_client(
    mock_embedding_service,
    mock_vector_store,
    mock_metadata_db,
    mock_object_store,
    mock_sentiment_service,
    mock_explainability_service,
):
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient
    from app.api.health import router as health_router
    from app.api.search import router as search_router
    from app.api.explain import router as explain_router

    app = FastAPI()
    app.include_router(health_router)
    app.include_router(search_router)
    app.include_router(explain_router)

    app.state.embedding_service = mock_embedding_service
    app.state.vector_store = mock_vector_store
    app.state.metadata_db = mock_metadata_db
    app.state.object_store = mock_object_store
    app.state.sentiment_service = mock_sentiment_service
    app.state.explainability_service = mock_explainability_service

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_sentiment_explain_returns_shap(explain_client):
    response = await explain_client.post("/api/explain/sentiment", json={
        "text": "Apple reported record Q4 revenue",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "positive"
    assert len(data["shap_values"]) == 2
    assert data["base_value"] == 0.33


@pytest.mark.asyncio
async def test_sentiment_explain_empty_text(explain_client, mock_explainability_service):
    mock_explainability_service.explain_sentiment.side_effect = ValueError(
        "Input text must not be empty"
    )
    response = await explain_client.post("/api/explain/sentiment", json={
        "text": "",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_retrieval_explain_returns_contributions(
    explain_client, mock_embedding_service, mock_vector_store
):
    mock_vector_store.client.retrieve = AsyncMock(return_value=[
        MagicMock(
            id="abc123",
            vector={"full": [0.1] * 3072},
            payload={"modality": "text", "text_preview": "Apple earnings"},
        )
    ])

    response = await explain_client.post("/api/explain/retrieval", json={
        "query": "Apple earnings growth",
        "result_ids": ["abc123"],
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "abc123"


@pytest.mark.asyncio
async def test_pipeline_returns_stages(explain_client):
    response = await explain_client.get("/api/explain/pipeline")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    assert data[0]["step"] == 1
    assert "name" in data[0]
    assert "description" in data[0]
