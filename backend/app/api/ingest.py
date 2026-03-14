"""
Ingestion API endpoints: accept file uploads and route to the ingestion pipeline.
"""

import logging

from fastapi import APIRouter, Form, Request, UploadFile

from app.models.schemas import IngestResponse
from app.services.ingest import IngestionPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["ingest"])


def _get_pipeline(request: Request) -> IngestionPipeline:
    """Build an IngestionPipeline from app state services."""
    state = request.app.state
    return IngestionPipeline(
        embedding_service=state.embedding_service,
        vector_store=state.vector_store,
        metadata_db=state.metadata_db,
        object_store=state.object_store,
    )


@router.post("/text", response_model=IngestResponse)
async def ingest_text(
    request: Request,
    file: UploadFile | None = None,
    text: str | None = Form(None),
    title: str = Form(...),
    source_type: str = Form(...),
    ticker: str | None = Form(None),
    published_at: str | None = Form(None),
):
    """Ingest a text document. Accept either a file upload or raw text in form data."""
    pipeline = _get_pipeline(request)

    if file:
        content = (await file.read()).decode("utf-8")
    elif text:
        content = text
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Provide either 'file' or 'text'")

    doc_id, chunk_count = await pipeline.ingest_text(
        text=content,
        title=title,
        source_type=source_type,
        ticker=ticker,
        published_at=published_at,
    )
    return IngestResponse(document_id=doc_id, chunk_count=chunk_count)


@router.post("/audio", response_model=IngestResponse)
async def ingest_audio(
    request: Request,
    file: UploadFile,
    title: str = Form(...),
    source_type: str = Form(...),
    ticker: str | None = Form(None),
    published_at: str | None = Form(None),
):
    """Ingest an audio file (earnings call recording)."""
    pipeline = _get_pipeline(request)
    audio_bytes = await file.read()

    doc_id, chunk_count = await pipeline.ingest_audio(
        audio_bytes=audio_bytes,
        filename=file.filename or "audio.mp4",
        title=title,
        source_type=source_type,
        ticker=ticker,
        published_at=published_at,
    )
    return IngestResponse(document_id=doc_id, chunk_count=chunk_count)


@router.post("/pdf", response_model=IngestResponse)
async def ingest_pdf(
    request: Request,
    file: UploadFile,
    title: str = Form(...),
    source_type: str = Form(...),
    ticker: str | None = Form(None),
    published_at: str | None = Form(None),
):
    """Ingest a PDF document (SEC filing)."""
    pipeline = _get_pipeline(request)
    pdf_bytes = await file.read()

    doc_id, chunk_count = await pipeline.ingest_pdf(
        pdf_bytes=pdf_bytes,
        filename=file.filename or "document.pdf",
        title=title,
        source_type=source_type,
        ticker=ticker,
        published_at=published_at,
    )
    return IngestResponse(document_id=doc_id, chunk_count=chunk_count)


@router.post("/image", response_model=IngestResponse)
async def ingest_image(
    request: Request,
    file: UploadFile,
    title: str = Form(...),
    source_type: str = Form(...),
    ticker: str | None = Form(None),
    published_at: str | None = Form(None),
):
    """Ingest an image (financial chart)."""
    pipeline = _get_pipeline(request)
    image_bytes = await file.read()

    doc_id, chunk_count = await pipeline.ingest_image(
        image_bytes=image_bytes,
        filename=file.filename or "chart.png",
        title=title,
        source_type=source_type,
        ticker=ticker,
        published_at=published_at,
    )
    return IngestResponse(document_id=doc_id, chunk_count=chunk_count)
