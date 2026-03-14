"""
Shared test fixtures: mocked services and FastAPI test client.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.schemas import HealthResponse


@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService returning deterministic vectors."""
    service = MagicMock()

    def make_vector(dims):
        return [0.1] * dims

    service.embed_text = AsyncMock(
        side_effect=lambda texts, **kw: [make_vector(kw.get("dimensions", 3072))] * len(texts)
    )
    service.embed_query = AsyncMock(
        side_effect=lambda query, **kw: make_vector(kw.get("dimensions", 3072))
    )
    service.embed_image = AsyncMock(
        side_effect=lambda paths, **kw: [make_vector(kw.get("dimensions", 3072))] * len(paths)
    )
    service.embed_audio = AsyncMock(
        side_effect=lambda path, **kw: make_vector(kw.get("dimensions", 3072))
    )
    service.embed_pdf = AsyncMock(
        side_effect=lambda path, **kw: make_vector(kw.get("dimensions", 3072))
    )
    return service


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore with in-memory storage."""
    store = MagicMock()
    store.ensure_collection = AsyncMock()
    store.upsert = AsyncMock(side_effect=lambda **kw: str(uuid.uuid4()))
    store.search = AsyncMock(return_value=[
        {
            "id": str(uuid.uuid4()),
            "score": 0.95,
            "payload": {
                "modality": "text",
                "source_type": "news",
                "ticker": "AAPL",
                "date": "2025-01-15",
                "text_preview": "Apple reported strong Q4 earnings...",
                "storage_key": "text/apple_q4.txt",
                "parent_doc_id": str(uuid.uuid4()),
                "chunk_index": 0,
            },
        }
    ])
    store.close = AsyncMock()
    store.client = MagicMock()
    store.client.get_collections = AsyncMock(return_value=[])
    return store


@pytest.fixture
def mock_metadata_db():
    """Mock MetadataDB."""
    db = MagicMock()
    db.create_tables = AsyncMock()
    db.create_document = AsyncMock(side_effect=lambda **kw: str(uuid.uuid4()))
    db.create_chunk = AsyncMock(side_effect=lambda **kw: str(uuid.uuid4()))
    db.update_chunk_count = AsyncMock()
    db.get_document = AsyncMock(return_value=None)
    db.get_chunks_by_document = AsyncMock(return_value=[])
    db.close = AsyncMock()
    db.engine = MagicMock()
    return db


@pytest.fixture
def mock_object_store():
    """Mock ObjectStore."""
    store = MagicMock()
    store.upload_file = AsyncMock(side_effect=lambda *args, **kw: args[1] if len(args) > 1 else kw.get("key", "unknown"))
    store.generate_presigned_url = AsyncMock(
        side_effect=lambda key, **kw: f"https://storage.example.com/{key}?signed=true"
    )
    return store


@pytest.fixture
async def app_client(
    mock_embedding_service,
    mock_vector_store,
    mock_metadata_db,
    mock_object_store,
):
    """FastAPI test client with mocked services."""
    from fastapi import FastAPI
    from app.api.health import router as health_router
    from app.api.search import router as search_router
    from app.api.ingest import router as ingest_router

    app = FastAPI()
    app.include_router(health_router)
    app.include_router(search_router)
    app.include_router(ingest_router)

    app.state.embedding_service = mock_embedding_service
    app.state.vector_store = mock_vector_store
    app.state.metadata_db = mock_metadata_db
    app.state.object_store = mock_object_store

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
