"""Tests for the EmbeddingService."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.embedding import EmbeddingService, TaskType


@pytest.fixture
def mock_genai_client():
    """Mock the google-genai client."""
    client = MagicMock()
    embedding = MagicMock()
    embedding.values = [0.1] * 3072

    response = MagicMock()
    response.embeddings = [embedding]

    client.models.embed_content = MagicMock(return_value=response)
    return client


@pytest.fixture
def embedding_service(mock_genai_client):
    service = EmbeddingService(api_key="test-key")
    service.client = mock_genai_client
    return service


@pytest.mark.asyncio
async def test_embed_text_returns_correct_dimensions(embedding_service, mock_genai_client):
    # Configure mock to return vectors of expected size
    embedding = MagicMock()
    embedding.values = [0.1] * 3072
    response = MagicMock()
    response.embeddings = [embedding]
    mock_genai_client.models.embed_content.return_value = response

    result = await embedding_service.embed_text(["test text"], dimensions=3072)

    assert len(result) == 1
    assert len(result[0]) == 3072


@pytest.mark.asyncio
async def test_embed_text_batch(embedding_service, mock_genai_client):
    texts = ["text 1", "text 2", "text 3"]
    embedding = MagicMock()
    embedding.values = [0.1] * 768
    response = MagicMock()
    response.embeddings = [embedding, embedding, embedding]
    mock_genai_client.models.embed_content.return_value = response

    result = await embedding_service.embed_text(texts, dimensions=768)

    assert len(result) == 3
    # Verify batch was sent as a single API call
    mock_genai_client.models.embed_content.assert_called_once()


@pytest.mark.asyncio
async def test_embed_query_uses_retrieval_query_task_type(embedding_service, mock_genai_client):
    embedding = MagicMock()
    embedding.values = [0.1] * 3072
    response = MagicMock()
    response.embeddings = [embedding]
    mock_genai_client.models.embed_content.return_value = response

    await embedding_service.embed_query("test query")

    call_kwargs = mock_genai_client.models.embed_content.call_args
    config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
    assert config.task_type == TaskType.RETRIEVAL_QUERY.value


@pytest.mark.asyncio
async def test_embed_image_enforces_batch_limit(embedding_service):
    from pathlib import Path

    fake_paths = [Path(f"/tmp/img_{i}.png") for i in range(7)]

    with pytest.raises(AssertionError, match="max 6"):
        await embedding_service.embed_image(fake_paths)


@pytest.mark.asyncio
async def test_retry_on_failure(embedding_service, mock_genai_client):
    """Verify exponential backoff retries on failure."""
    embedding = MagicMock()
    embedding.values = [0.1] * 3072
    success_response = MagicMock()
    success_response.embeddings = [embedding]

    # Fail twice, succeed on third try
    mock_genai_client.models.embed_content.side_effect = [
        Exception("rate limit"),
        Exception("rate limit"),
        success_response,
    ]

    with patch("app.services.embedding.asyncio.sleep", new_callable=AsyncMock):
        result = await embedding_service.embed_query("test")
        assert len(result) == 3072
