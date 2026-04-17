"""Tests for the search endpoint."""

import pytest


@pytest.mark.asyncio
async def test_search_returns_results(
    app_client, mock_embedding_service, mock_vector_store, mock_object_store
):
    response = await app_client.post("/api/search/", json={
        "query": "bearish signals from Q4 tech earnings",
        "limit": 10,
    })
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0

    # Verify result shape
    r = results[0]
    assert "id" in r
    assert "score" in r
    assert "modality" in r
    assert "source_type" in r
    assert "storage_key" in r
    # storage_key should be a presigned URL
    assert "signed=true" in r["storage_key"]


@pytest.mark.asyncio
async def test_search_calls_embed_query(app_client, mock_embedding_service):
    await app_client.post("/api/search/", json={
        "query": "tech earnings",
        "limit": 5,
    })
    mock_embedding_service.embed_query.assert_called()


@pytest.mark.asyncio
async def test_search_compact_uses_768_dims(app_client, mock_embedding_service):
    await app_client.post("/api/search/", json={
        "query": "revenue growth",
        "use_compact": True,
        "limit": 5,
    })
    call_kwargs = mock_embedding_service.embed_query.call_args
    assert call_kwargs.kwargs.get("dimensions") == 768 or call_kwargs[1].get("dimensions") == 768
