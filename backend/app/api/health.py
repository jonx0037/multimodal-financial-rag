"""Health check endpoint with Qdrant and PostgreSQL connectivity checks."""

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.models.schemas import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    qdrant_ok = False
    postgres_ok = False

    # Check Qdrant
    try:
        vector_store = request.app.state.vector_store
        await vector_store.client.get_collections()
        qdrant_ok = True
    except Exception:
        pass

    # Check PostgreSQL
    try:
        metadata_db = request.app.state.metadata_db
        async with metadata_db.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        postgres_ok = True
    except Exception:
        pass

    status = "ok" if (qdrant_ok and postgres_ok) else "degraded"
    return HealthResponse(
        status=status,
        version="0.1.0",
        qdrant_connected=qdrant_ok,
        postgres_connected=postgres_ok,
    )
