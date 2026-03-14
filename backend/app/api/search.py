"""
Search API endpoint: embed query → search Qdrant → hydrate metadata → return results.
"""

from fastapi import APIRouter, Request

from app.models.schemas import SearchRequest, SearchResult

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/", response_model=list[SearchResult])
async def search(req: SearchRequest, request: Request) -> list[SearchResult]:
    """Multimodal semantic search with per-modality balanced retrieval."""
    embedding_service = request.app.state.embedding_service
    vector_store = request.app.state.vector_store
    object_store = request.app.state.object_store

    dims = 768 if req.use_compact else 3072
    query_vector = await embedding_service.embed_query(req.query, dimensions=dims)

    # Determine which modalities to search
    modalities = req.modalities or ["text", "audio", "pdf", "image"]
    per_modality_limit = max(1, req.limit // len(modalities))

    # Run one search per modality, collect all results
    all_results: list[dict] = []
    for modality in modalities:
        results = await vector_store.search(
            query_vector=query_vector,
            limit=per_modality_limit,
            modality_filter=modality,
            ticker_filter=req.tickers[0] if req.tickers else None,
            date_after=req.date_after,
            date_before=req.date_before,
            use_compact=req.use_compact,
        )
        all_results.extend(results)

    # Re-sort merged results by score descending
    all_results.sort(key=lambda r: r["score"], reverse=True)

    # Trim to requested limit and build response
    trimmed = all_results[: req.limit]

    search_results = []
    for r in trimmed:
        payload = r["payload"]
        presigned_url = await object_store.generate_presigned_url(
            payload["storage_key"]
        )
        search_results.append(SearchResult(
            id=r["id"],
            score=r["score"],
            modality=payload["modality"],
            source_type=payload["source_type"],
            ticker=payload.get("ticker"),
            date=payload.get("date"),
            text_preview=payload.get("text_preview"),
            storage_key=presigned_url,
        ))

    return search_results