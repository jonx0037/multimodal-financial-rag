"""
Explain API endpoints: sentiment SHAP, retrieval explanation, pipeline stages.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import (
    PipelineStage,
    RetrievalExplainRequest,
    RetrievalExplainResponse,
    ResultExplanation,
    QueryTermContribution,
    SentimentExplainRequest,
    SentimentExplainResponse,
    ShapToken,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/explain", tags=["explain"])

PIPELINE_STAGES = [
    PipelineStage(
        step=1,
        name="Parse Query",
        description="Your natural language query is received and prepared for embedding.",
        details={"input": "raw text query"},
    ),
    PipelineStage(
        step=2,
        name="Embed Query",
        description=(
            "The query is converted into a dense vector using Google Gemini Embedding 2. "
            "This captures the semantic meaning of your query, not just keywords."
        ),
        details={
            "model": "gemini-embedding-2-preview",
            "dimensions": 3072,
            "compact_dimensions": 768,
        },
    ),
    PipelineStage(
        step=3,
        name="Vector Search",
        description=(
            "The query vector is compared against all document vectors in Qdrant using "
            "cosine similarity. Documents whose embeddings are closest to your query are retrieved."
        ),
        details={
            "database": "Qdrant Cloud",
            "metric": "cosine similarity",
            "index_type": "HNSW",
        },
    ),
    PipelineStage(
        step=4,
        name="Balance by Modality",
        description=(
            "Results are balanced across modalities (text, audio, PDF, image) so no "
            "single type dominates. The result limit is split evenly across requested modalities."
        ),
        details={"modalities": ["text", "audio", "pdf", "image"]},
    ),
    PipelineStage(
        step=5,
        name="Rank Results",
        description=(
            "All results from each modality search are merged and re-sorted by similarity "
            "score. The top results across all modalities are returned."
        ),
        details={"sort": "descending by cosine similarity score"},
    ),
    PipelineStage(
        step=6,
        name="Generate URLs",
        description=(
            "For each result, a time-limited presigned URL is generated so you can "
            "access the original document (earnings call audio, SEC filing PDF, etc.)."
        ),
        details={"url_type": "presigned", "storage": "S3-compatible (Cloudflare R2)"},
    ),
]


@router.post("/sentiment", response_model=SentimentExplainResponse)
async def explain_sentiment(req: SentimentExplainRequest, request: Request):
    """Compute SHAP token attributions for FinBERT sentiment prediction."""
    explainability = request.app.state.explainability_service

    try:
        result = await asyncio.to_thread(explainability.explain_sentiment, req.text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return SentimentExplainResponse(
        label=result["label"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        shap_values=[ShapToken(**sv) for sv in result["shap_values"]],
        base_value=result["base_value"],
    )


@router.post("/retrieval", response_model=RetrievalExplainResponse)
async def explain_retrieval(req: RetrievalExplainRequest, request: Request):
    """Explain why specific results matched the query."""
    embedding_service = request.app.state.embedding_service
    vector_store = request.app.state.vector_store
    explainability = request.app.state.explainability_service

    query_vector = await embedding_service.embed_query(req.query)
    query_terms = req.query.strip().split()

    points = await vector_store.client.retrieve(
        collection_name=vector_store.collection,
        ids=req.result_ids,
        with_vectors=True,
        with_payload=True,
    )

    results = []
    for point in points:
        result_vector = point.vector.get("full", point.vector.get("compact", []))
        modality = point.payload.get("modality", "unknown")

        explanation = explainability.explain_retrieval_result(
            query_terms=query_terms,
            query_vector=query_vector,
            result_vector=result_vector,
            result_id=str(point.id),
            score=0.0,
            modality=modality,
            use_compact="compact" in point.vector,
        )
        results.append(
            ResultExplanation(
                id=explanation["id"],
                score=explanation["score"],
                query_terms_contribution=[
                    QueryTermContribution(**c)
                    for c in explanation["query_terms_contribution"]
                ],
                modality=explanation["modality"],
                similarity_method=explanation["similarity_method"],
            )
        )

    return RetrievalExplainResponse(results=results)


@router.get("/pipeline", response_model=list[PipelineStage])
async def get_pipeline():
    """Return the RAG pipeline stages for educational display."""
    return PIPELINE_STAGES
