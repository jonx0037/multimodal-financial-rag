"""
Pydantic request/response models for the API layer.
"""

from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    modalities: list[str] | None = None  # filter: ["text", "audio", "pdf", "image"]
    tickers: list[str] | None = None  # filter: ["AAPL", "MSFT"]
    date_after: str | None = None  # ISO 8601
    date_before: str | None = None
    limit: int = 10
    use_compact: bool = False  # use 768-dim for faster search


class SearchResult(BaseModel):
    id: str
    score: float
    modality: str
    source_type: str
    ticker: str | None = None
    date: str | None = None
    text_preview: str | None = None
    storage_key: str


class IngestResponse(BaseModel):
    document_id: str
    chunk_count: int


class HealthResponse(BaseModel):
    status: str
    version: str
    qdrant_connected: bool = False
    postgres_connected: bool = False


class ShapToken(BaseModel):
    token: str
    value: float


class SentimentExplainRequest(BaseModel):
    text: str


class SentimentExplainResponse(BaseModel):
    label: str
    confidence: float
    probabilities: dict[str, float]
    shap_values: list[ShapToken]
    base_value: float


class QueryTermContribution(BaseModel):
    term: str
    weight: float


class ResultExplanation(BaseModel):
    id: str
    score: float
    query_terms_contribution: list[QueryTermContribution]
    modality: str
    similarity_method: str


class RetrievalExplainRequest(BaseModel):
    query: str
    result_ids: list[str]


class RetrievalExplainResponse(BaseModel):
    results: list[ResultExplanation]


class PipelineStage(BaseModel):
    step: int
    name: str
    description: str
    details: dict | None = None
