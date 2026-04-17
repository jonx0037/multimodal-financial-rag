"""Tests for the explain API endpoints."""

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_sentiment_explain_returns_shap(app_client):
    response = await app_client.post("/api/explain/sentiment", json={
        "text": "Apple reported record Q4 revenue",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "positive"
    assert len(data["shap_values"]) >= 1
    assert data["base_value"] == 0.33


@pytest.mark.asyncio
async def test_sentiment_explain_empty_text(app_client, mock_explainability_service):
    mock_explainability_service.explain_sentiment.side_effect = ValueError(
        "Input text must not be empty"
    )
    response = await app_client.post("/api/explain/sentiment", json={
        "text": "",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_retrieval_explain_returns_contributions(
    app_client, mock_embedding_service, mock_vector_store
):
    mock_vector_store.client.retrieve = AsyncMock(return_value=[
        MagicMock(
            id="abc123",
            vector={"full": [0.1] * 3072},
            payload={"modality": "text", "text_preview": "Apple earnings"},
        )
    ])

    response = await app_client.post("/api/explain/retrieval", json={
        "query": "Apple earnings growth",
        "result_ids": ["abc123"],
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "abc123"


@pytest.mark.asyncio
async def test_pipeline_returns_stages(app_client):
    response = await app_client.get("/api/explain/pipeline")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    assert data[0]["step"] == 1
    assert "name" in data[0]
    assert "description" in data[0]
