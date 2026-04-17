import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client.models import Distance, VectorParams

from app.api.explain import router as explain_router
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.search import router as search_router
from app.config import get_settings
from app.services.embedding import EmbeddingService
from app.services.metadata import MetadataDB
from app.services.storage import ObjectStore
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

COLLECTION_NAME = "financial_docs"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level))

    # Initialize services
    embedding_service = EmbeddingService(api_key=settings.gemini_api_key)
    vector_store = VectorStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection=COLLECTION_NAME,
    )
    metadata_db = MetadataDB(database_url=settings.async_database_url)
    object_store = ObjectStore(
        endpoint_url=settings.s3_endpoint_url,
        access_key_id=settings.s3_access_key_id,
        secret_access_key=settings.s3_secret_access_key,
        bucket_name=settings.s3_bucket_name,
    )

    # Create Qdrant collection if it doesn't exist
    await vector_store.ensure_collection(
        vectors_config={
            "full": VectorParams(size=3072, distance=Distance.COSINE),
            "compact": VectorParams(size=768, distance=Distance.COSINE),
        }
    )

    # Create payload indexes for Qdrant Cloud filtered search
    await vector_store.ensure_payload_indexes()

    # Create database tables
    await metadata_db.create_tables()

    # Attach services to app state
    app.state.embedding_service = embedding_service
    app.state.vector_store = vector_store
    app.state.metadata_db = metadata_db
    app.state.object_store = object_store

    # Explainability services (FinBERT + SHAP) require ~1GB RAM
    # Disabled by default on memory-constrained deployments (Fly.io 512MB)
    if settings.enable_explainability:
        from app.services.explainability import ExplainabilityService
        from app.services.sentiment import SentimentService

        sentiment_service = SentimentService()
        explainability_service = ExplainabilityService(sentiment_service)
        app.state.sentiment_service = sentiment_service
        app.state.explainability_service = explainability_service
        logger.info("Explainability services loaded (FinBERT + SHAP)")
    else:
        app.state.sentiment_service = None
        app.state.explainability_service = None
        logger.info("Explainability services disabled (set ENABLE_EXPLAINABILITY=true to enable)")

    logger.info("All services initialized successfully")
    yield

    # Cleanup
    await vector_store.close()
    await metadata_db.close()
    logger.info("Services shut down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Multimodal Financial RAG",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(search_router)
    app.include_router(ingest_router)
    app.include_router(explain_router)

    return app


app = create_app()
