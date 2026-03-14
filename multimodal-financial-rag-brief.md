# Claude Code Handoff Brief: Multimodal Financial RAG with Gemini Embedding 2

**Project:** `multimodal-financial-rag`
**Author:** Jonathan Rocha
**Date:** 2026-03-13
**Status:** Scaffolding Ready

---

## 1. Project Overview

Build a multimodal Retrieval-Augmented Generation (RAG) system for financial document search and analysis, powered by Google's Gemini Embedding 2 model. The system embeds earnings call audio, SEC filing PDFs, financial chart images, and news article text into a single unified vector space, enabling cross-modal semantic search over financial data.

### Value Proposition

- **market-sentiment.io extension:** Adds a multimodal RAG layer to the existing capstone sentiment regime detection system
- **DataSalt portfolio piece:** Production-grade case study for datasalt.ai showcasing multimodal AI in a financial vertical
- **Book chapter material:** Reference implementation for *Applied NLP for Finance* (Chapters 10–12 territory)

### Core Capability

A user query like _"show me bearish signals from Q4 tech earnings"_ retrieves:
- A relevant segment of a CEO's earnings call **audio**
- The risk factors section of a 10-K **PDF**
- A candlestick chart showing the selloff as an **image**
- The Reuters article covering the event as **text**

All ranked by cosine similarity in a single embedding space.

---

## 2. Architecture

### 2.1 High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js 14 Frontend                     │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Search UI │  │ Results Grid │  │ Multimodal Previewer  │  │
│  └─────┬────┘  └──────┬───────┘  └───────────┬───────────┘  │
│        └──────────────┼───────────────────────┘              │
│                       │ REST / WebSocket                     │
└───────────────────────┼─────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────┐
│                  FastAPI Backend                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │
│  │ /api/search│  │ /api/ingest│  │ /api/embed             │ │
│  └─────┬──────┘  └─────┬──────┘  └──────────┬─────────────┘ │
│        │               │                     │               │
│  ┌─────┴───────────────┴─────────────────────┴─────────┐    │
│  │              Embedding Service Layer                 │    │
│  │   (google-genai SDK → Gemini Embedding 2 API)       │    │
│  └─────────────────────────┬───────────────────────────┘    │
│                             │                                │
│  ┌──────────────────────────┴──────────────────────────┐    │
│  │              Vector Store Adapter                    │    │
│  │   (Qdrant Cloud — 3072-dim cosine similarity)       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Document Store (PostgreSQL / Railway)        │    │
│  │   (metadata, raw file refs, chunk mappings)          │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼─────────────────────────────────────┐
│              Object Storage (S3 / R2)                       │
│   audio/, pdfs/, images/, articles/                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | Next.js 14 (App Router) + Tailwind CSS | Matches existing datasalt.ai and market-sentiment.io stacks |
| Backend | FastAPI (Python 3.11+) | Matches market-sentiment.io backend; async-native |
| Embeddings | `google-genai` Python SDK → `gemini-embedding-002` | Gemini Embedding 2 via Gemini API (free tier for prototyping) |
| Vector DB | Qdrant Cloud (free tier) | Native 3072-dim support, listed as official integration, REST + gRPC |
| Metadata DB | PostgreSQL on Railway | Consistent with existing market-sentiment.io infra |
| Object Storage | Cloudflare R2 (free egress) or AWS S3 | Raw file storage for audio, PDFs, images |
| Deployment | Railway (backend) + Vercel (frontend) | Consistent with existing deployment patterns |

### 2.3 Why Qdrant over pgvector

- pgvector works fine for 768-dim or 1536-dim, but 3072-dim vectors at scale benefit from a purpose-built vector DB
- Qdrant supports named vectors (we can store both full 3072 and reduced 768 per document)
- Built-in payload filtering (filter by modality, ticker, date range before similarity search)
- Free cloud tier is sufficient for prototyping; self-hosted option on Railway if needed

---

## 3. Data Model

### 3.1 Document Types & Ingestion

| Modality | Source | Chunking Strategy | Gemini Embedding 2 Config |
|----------|--------|-------------------|---------------------------|
| **Text** | News articles (RSS/API), earnings transcripts | 512-token sliding window, 128-token overlap | `input_type: "RETRIEVAL_DOCUMENT"`, up to 8192 tokens |
| **Audio** | Earnings call recordings (MP3/WAV → MP4) | 60-second segments with 10s overlap | Up to 120s per request, native audio (no transcription) |
| **PDF** | SEC filings (10-K, 10-Q, 8-K) | Per-page or per-section (up to 6 pages per request) | Direct PDF embedding |
| **Image** | Financial charts, candlestick screenshots | Full image per embedding (no chunking) | PNG/JPEG, up to 6 images per request |

### 3.2 Qdrant Collection Schema

```python
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType

COLLECTION_CONFIG = {
    "collection_name": "financial_docs",
    "vectors_config": {
        "full": VectorParams(size=3072, distance=Distance.COSINE),
        "compact": VectorParams(size=768, distance=Distance.COSINE),
    },
    "payload_schema": {
        "modality": PayloadSchemaType.KEYWORD,      # text | audio | pdf | image
        "ticker": PayloadSchemaType.KEYWORD,         # AAPL, MSFT, etc.
        "source_type": PayloadSchemaType.KEYWORD,    # earnings_call | sec_filing | news | chart
        "date": PayloadSchemaType.DATETIME,          # publication/filing date
        "chunk_index": PayloadSchemaType.INTEGER,    # position within parent doc
        "parent_doc_id": PayloadSchemaType.KEYWORD,  # FK to PostgreSQL
        "text_preview": PayloadSchemaType.TEXT,       # first 500 chars for display
        "storage_key": PayloadSchemaType.KEYWORD,    # S3/R2 object key
    }
}
```

### 3.3 PostgreSQL Metadata Schema

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    modality VARCHAR(10) NOT NULL CHECK (modality IN ('text', 'audio', 'pdf', 'image')),
    source_type VARCHAR(20) NOT NULL,
    ticker VARCHAR(10),
    published_at TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    storage_key TEXT NOT NULL,          -- S3/R2 path
    file_size_bytes BIGINT,
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb  -- flexible fields per source
);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    qdrant_point_id UUID NOT NULL,      -- matches Qdrant point ID
    text_preview TEXT,                   -- first 500 chars (null for audio/image)
    start_offset INTEGER,               -- token offset for text, seconds for audio
    end_offset INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_ticker ON documents(ticker);
CREATE INDEX idx_documents_modality ON documents(modality);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
```

---

## 4. Core Modules

### 4.1 Embedding Service (`app/services/embedding.py`)

```python
"""
Wraps the google-genai SDK for Gemini Embedding 2.
Handles all modality-specific embedding logic.
"""
import google.genai as genai
from google.genai import types
from enum import Enum
from pathlib import Path

class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    PDF = "pdf"

class TaskType(str, Enum):
    RETRIEVAL_DOCUMENT = "RETRIEVAL_DOCUMENT"
    RETRIEVAL_QUERY = "RETRIEVAL_QUERY"
    SEMANTIC_SIMILARITY = "SEMANTIC_SIMILARITY"
    CLASSIFICATION = "CLASSIFICATION"
    CLUSTERING = "CLUSTERING"

class EmbeddingService:
    MODEL = "gemini-embedding-002"
    DEFAULT_DIMS = 3072
    COMPACT_DIMS = 768

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def embed_text(
        self,
        texts: list[str],
        task_type: TaskType = TaskType.RETRIEVAL_DOCUMENT,
        dimensions: int = DEFAULT_DIMS,
    ) -> list[list[float]]:
        """Embed one or more text chunks."""
        result = self.client.models.embed_content(
            model=self.MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type=task_type.value,
                output_dimensionality=dimensions,
            ),
        )
        return [e.values for e in result.embeddings]

    async def embed_image(
        self,
        image_paths: list[Path],
        task_type: TaskType = TaskType.RETRIEVAL_DOCUMENT,
        dimensions: int = DEFAULT_DIMS,
    ) -> list[list[float]]:
        """Embed up to 6 images per request."""
        parts = []
        for path in image_paths[:6]:
            img_bytes = path.read_bytes()
            mime = "image/png" if path.suffix == ".png" else "image/jpeg"
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
        result = self.client.models.embed_content(
            model=self.MODEL,
            contents=parts,
            config=types.EmbedContentConfig(
                task_type=task_type.value,
                output_dimensionality=dimensions,
            ),
        )
        return [e.values for e in result.embeddings]

    async def embed_audio(
        self,
        audio_path: Path,
        task_type: TaskType = TaskType.RETRIEVAL_DOCUMENT,
        dimensions: int = DEFAULT_DIMS,
    ) -> list[float]:
        """Embed audio segment (up to 120s). Native — no transcription."""
        audio_bytes = audio_path.read_bytes()
        mime = "audio/mp4"  # convert source to mp4 before calling
        result = self.client.models.embed_content(
            model=self.MODEL,
            contents=[types.Part.from_bytes(data=audio_bytes, mime_type=mime)],
            config=types.EmbedContentConfig(
                task_type=task_type.value,
                output_dimensionality=dimensions,
            ),
        )
        return result.embeddings[0].values

    async def embed_pdf(
        self,
        pdf_path: Path,
        task_type: TaskType = TaskType.RETRIEVAL_DOCUMENT,
        dimensions: int = DEFAULT_DIMS,
    ) -> list[float]:
        """Embed PDF directly (up to 6 pages)."""
        pdf_bytes = pdf_path.read_bytes()
        result = self.client.models.embed_content(
            model=self.MODEL,
            contents=[types.Part.from_bytes(
                data=pdf_bytes, mime_type="application/pdf"
            )],
            config=types.EmbedContentConfig(
                task_type=task_type.value,
                output_dimensionality=dimensions,
            ),
        )
        return result.embeddings[0].values

    async def embed_query(
        self,
        query: str,
        dimensions: int = DEFAULT_DIMS,
    ) -> list[float]:
        """Embed a search query (uses RETRIEVAL_QUERY task type)."""
        result = self.client.models.embed_content(
            model=self.MODEL,
            contents=[query],
            config=types.EmbedContentConfig(
                task_type=TaskType.RETRIEVAL_QUERY.value,
                output_dimensionality=dimensions,
            ),
        )
        return result.embeddings[0].values
```

### 4.2 Vector Store Adapter (`app/services/vector_store.py`)

```python
"""
Qdrant adapter. Handles upsert, search, and filtering.
Abstract enough to swap for pgvector if needed.
"""
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct, Filter, FieldCondition, MatchValue,
    DatetimeRange, SearchParams, NamedVector
)
from uuid import uuid4

class VectorStore:
    def __init__(self, url: str, api_key: str, collection: str = "financial_docs"):
        self.client = AsyncQdrantClient(url=url, api_key=api_key)
        self.collection = collection

    async def upsert(
        self,
        full_vector: list[float],
        compact_vector: list[float],
        payload: dict,
    ) -> str:
        point_id = str(uuid4())
        await self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(
                id=point_id,
                vector={
                    "full": full_vector,
                    "compact": compact_vector,
                },
                payload=payload,
            )],
        )
        return point_id

    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        modality_filter: str | None = None,
        ticker_filter: str | None = None,
        date_after: str | None = None,
        date_before: str | None = None,
        use_compact: bool = False,
    ) -> list[dict]:
        conditions = []
        if modality_filter:
            conditions.append(FieldCondition(
                key="modality", match=MatchValue(value=modality_filter)
            ))
        if ticker_filter:
            conditions.append(FieldCondition(
                key="ticker", match=MatchValue(value=ticker_filter.upper())
            ))
        if date_after or date_before:
            conditions.append(FieldCondition(
                key="date",
                range=DatetimeRange(gte=date_after, lte=date_before),
            ))

        vector_name = "compact" if use_compact else "full"
        results = await self.client.search(
            collection_name=self.collection,
            query_vector=NamedVector(name=vector_name, vector=query_vector),
            query_filter=Filter(must=conditions) if conditions else None,
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]
```

### 4.3 Ingestion Pipeline (`app/services/ingest.py`)

```python
"""
Orchestrates: file upload → chunking → embedding → vector upsert → metadata write.
Each modality has its own chunking strategy.
"""

class IngestionPipeline:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        metadata_db: MetadataDB,       # SQLAlchemy async session wrapper
        object_store: ObjectStore,      # S3/R2 wrapper
    ):
        self.embed = embedding_service
        self.vectors = vector_store
        self.meta = metadata_db
        self.storage = object_store

    async def ingest_text(self, text: str, metadata: dict) -> str:
        """Chunk text with sliding window, embed all chunks, upsert."""
        chunks = self._chunk_text(text, window=512, overlap=128)
        doc_id = await self.meta.create_document(metadata, chunk_count=len(chunks))

        for i, chunk in enumerate(chunks):
            full_vec = (await self.embed.embed_text([chunk], dimensions=3072))[0]
            compact_vec = (await self.embed.embed_text([chunk], dimensions=768))[0]
            point_id = await self.vectors.upsert(
                full_vector=full_vec,
                compact_vector=compact_vec,
                payload={
                    "modality": "text",
                    "chunk_index": i,
                    "parent_doc_id": doc_id,
                    "text_preview": chunk[:500],
                    **metadata,
                },
            )
            await self.meta.create_chunk(doc_id, i, point_id, chunk[:500])
        return doc_id

    async def ingest_audio(self, audio_path: Path, metadata: dict) -> str:
        """Segment audio into 60s chunks with 10s overlap, embed each."""
        segments = await self._segment_audio(audio_path, duration=60, overlap=10)
        doc_id = await self.meta.create_document(metadata, chunk_count=len(segments))

        for i, seg_path in enumerate(segments):
            full_vec = await self.embed.embed_audio(seg_path, dimensions=3072)
            compact_vec = await self.embed.embed_audio(seg_path, dimensions=768)
            point_id = await self.vectors.upsert(
                full_vector=full_vec,
                compact_vector=compact_vec,
                payload={
                    "modality": "audio",
                    "chunk_index": i,
                    "parent_doc_id": doc_id,
                    "start_offset": i * 50,  # 60s - 10s overlap
                    **metadata,
                },
            )
            await self.meta.create_chunk(doc_id, i, point_id, start_offset=i*50)
        return doc_id

    # Similar methods: ingest_pdf(), ingest_image()
    # PDF: split into ≤6-page chunks, embed each chunk
    # Image: embed full image, one embedding per image

    @staticmethod
    def _chunk_text(text: str, window: int = 512, overlap: int = 128) -> list[str]:
        """Sliding window tokenizer-aware chunking."""
        # Implementation: use tiktoken or simple word-based splitting
        # Returns list of text chunks
        ...

    @staticmethod
    async def _segment_audio(path: Path, duration: int = 60, overlap: int = 10) -> list[Path]:
        """Use ffmpeg to split audio into overlapping segments."""
        # ffmpeg -i input.mp4 -f segment -segment_time 60 -segment_overlap 10 seg_%03d.mp4
        ...
```

### 4.4 Search API (`app/api/search.py`)

```python
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/search", tags=["search"])

class SearchRequest(BaseModel):
    query: str
    modalities: list[str] | None = None     # filter: ["text", "audio", "pdf", "image"]
    tickers: list[str] | None = None        # filter: ["AAPL", "MSFT"]
    date_after: str | None = None           # ISO 8601
    date_before: str | None = None
    limit: int = 10
    use_compact: bool = False               # use 768-dim for faster search

class SearchResult(BaseModel):
    id: str
    score: float
    modality: str
    source_type: str
    ticker: str | None
    date: str | None
    text_preview: str | None
    storage_key: str                        # presigned URL for frontend to fetch

@router.post("/", response_model=list[SearchResult])
async def search(req: SearchRequest):
    """
    1. Embed query with RETRIEVAL_QUERY task type
    2. Search Qdrant with optional filters
    3. Hydrate results with metadata from PostgreSQL
    4. Generate presigned URLs for media files
    5. Return ranked, multimodal results
    """
    ...
```

---

## 5. Frontend Components

### 5.1 Key Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `SearchPage` | Main search interface with query input and filter controls |
| `/results` | `ResultsGrid` | Masonry-style grid showing mixed-modality results |
| `/doc/[id]` | `DocumentViewer` | Full document viewer with modality-specific rendering |

### 5.2 ResultCard Component Variants

Each search result renders as a card with modality-specific preview:

- **TextCard:** Highlighted text snippet with relevance score badge
- **AudioCard:** Waveform visualization + inline audio player, timestamp of matched segment
- **PDFCard:** Thumbnail of matched page with highlighted section
- **ImageCard:** Chart/image thumbnail with caption overlay

### 5.3 Filter Bar

- Modality toggle buttons (Text / Audio / PDF / Image) — multi-select
- Ticker autocomplete (searchable dropdown)
- Date range picker
- Dimension toggle (Full 3072 vs Compact 768) — for demo/comparison purposes

---

## 6. Project Structure

```
multimodal-financial-rag/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app factory
│   │   ├── config.py                  # Pydantic Settings (env vars)
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── search.py              # POST /api/search
│   │   │   ├── ingest.py              # POST /api/ingest/{modality}
│   │   │   └── health.py              # GET /api/health
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── embedding.py           # Gemini Embedding 2 wrapper
│   │   │   ├── vector_store.py        # Qdrant adapter
│   │   │   ├── ingest.py              # Ingestion pipeline orchestrator
│   │   │   ├── metadata.py            # PostgreSQL metadata CRUD
│   │   │   └── storage.py             # S3/R2 object store wrapper
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── document.py            # SQLAlchemy models
│   │   │   └── schemas.py             # Pydantic request/response models
│   │   └── utils/
│   │       ├── chunking.py            # Text chunking utilities
│   │       └── audio.py               # ffmpeg audio segmentation
│   ├── alembic/                       # DB migrations
│   ├── tests/
│   │   ├── test_embedding.py
│   │   ├── test_ingest.py
│   │   └── test_search.py
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx               # SearchPage
│   │   │   ├── results/
│   │   │   │   └── page.tsx           # ResultsGrid
│   │   │   └── doc/
│   │   │       └── [id]/
│   │   │           └── page.tsx       # DocumentViewer
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── FilterBar.tsx
│   │   │   ├── ResultCard.tsx          # Dynamic card by modality
│   │   │   ├── TextCard.tsx
│   │   │   ├── AudioCard.tsx
│   │   │   ├── PDFCard.tsx
│   │   │   ├── ImageCard.tsx
│   │   │   └── WaveformPlayer.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                 # Fetch wrapper for backend
│   │   │   └── types.ts              # TypeScript interfaces
│   │   └── hooks/
│   │       ├── useSearch.ts
│   │       └── useDebounce.ts
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── package.json
│   └── tsconfig.json
├── scripts/
│   ├── seed_demo_data.py              # Ingest sample docs for demo
│   ├── download_earnings_calls.py     # Fetch from public sources
│   └── screenshot_charts.py           # Generate chart images via yfinance + matplotlib
├── docker-compose.yml                 # Local dev: Qdrant + PostgreSQL
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 7. Environment Variables

```bash
# .env.example

# Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Qdrant Cloud
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key

# PostgreSQL (Railway)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/multimodal_rag

# Object Storage (R2 or S3)
S3_ENDPOINT_URL=https://your-account.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your_access_key
S3_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=financial-docs

# App
CORS_ORIGINS=http://localhost:3000,https://rag.datasalt.ai
LOG_LEVEL=INFO
```

---

## 8. Execution Order for Claude Code

### Phase 1: Backend Scaffolding
1. Initialize `backend/` with `pyproject.toml` (dependencies: `fastapi`, `uvicorn`, `google-genai`, `qdrant-client`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `boto3`, `python-dotenv`, `pydantic-settings`)
2. Create `app/config.py` with Pydantic Settings loading from `.env`
3. Create `app/main.py` FastAPI app with CORS, lifespan (init Qdrant collection on startup)
4. Implement `app/services/embedding.py` — the `EmbeddingService` class exactly as specified in §4.1
5. Implement `app/services/vector_store.py` — the `VectorStore` class as specified in §4.2
6. Implement `app/models/document.py` — SQLAlchemy async models per §3.3
7. Implement `app/services/metadata.py` — CRUD wrapper around SQLAlchemy models
8. Implement `app/services/storage.py` — S3-compatible object store (upload, presigned URL generation)
9. Implement `app/services/ingest.py` — `IngestionPipeline` per §4.3
10. Implement `app/api/` routes — search (§4.4), ingest, health
11. Set up Alembic with initial migration
12. Create `Dockerfile` and `docker-compose.yml` (Qdrant + PostgreSQL for local dev)
13. Write tests for the embedding service (mock API), the ingest pipeline, and the search endpoint

### Phase 2: Frontend Scaffolding
1. Initialize `frontend/` with `npx create-next-app@latest` (App Router, TypeScript, Tailwind)
2. Create `lib/types.ts` with TypeScript interfaces matching backend Pydantic models
3. Create `lib/api.ts` fetch wrapper
4. Build `SearchBar` and `FilterBar` components
5. Build modality-specific cards: `TextCard`, `AudioCard`, `PDFCard`, `ImageCard`
6. Build `ResultCard` dynamic dispatcher
7. Wire up `SearchPage` → `ResultsGrid` flow
8. Build `DocumentViewer` page with modality-specific rendering
9. Add `WaveformPlayer` component (use `wavesurfer.js`)

### Phase 3: Demo Data & Integration
1. Create `scripts/seed_demo_data.py` — ingest 5-10 sample documents per modality
2. Create `scripts/download_earnings_calls.py` — fetch from public earnings call archives
3. Create `scripts/screenshot_charts.py` — generate candlestick charts with yfinance + matplotlib
4. End-to-end integration test: ingest → search → render

### Phase 4: Deployment
1. Railway: deploy backend with PostgreSQL addon
2. Qdrant Cloud: provision a free-tier cluster, run collection init
3. Vercel: deploy frontend, set `NEXT_PUBLIC_API_URL` env var
4. Optional: Set up `rag.datasalt.ai` subdomain pointing to Vercel

---

## 9. Key Implementation Notes

### Gemini Embedding 2 Specifics
- **Model string:** `gemini-embedding-002` (not `text-embedding-004`, that's the old text-only model)
- **Task types matter:** Always use `RETRIEVAL_DOCUMENT` for indexing, `RETRIEVAL_QUERY` for search queries — this significantly impacts retrieval quality
- **MRL dimensions:** Recommended tiers are 3072 (full), 1536 (balanced), 768 (compact). Store both 3072 and 768 in Qdrant named vectors for A/B comparison
- **Interleaved input:** For future enhancement, you can pass image + text together (e.g., chart image + caption) as a single embedding request for richer representations
- **Rate limits:** Free tier has request-per-minute limits. Implement exponential backoff in the embedding service. Batch text embeddings (multiple texts per request) to stay within limits
- **Audio format:** Convert all audio to MP4 before embedding. Use ffmpeg: `ffmpeg -i input.mp3 -c:a aac output.mp4`

### Audio Segmentation
- Use `ffmpeg` for splitting: `ffmpeg -i input.mp4 -f segment -segment_time 60 -c copy seg_%03d.mp4`
- 10-second overlap ensures we don't lose context at segment boundaries
- Store `start_offset` in metadata so the frontend can seek to the right timestamp

### Chunking Philosophy
- Text: 512-token window is the sweet spot for financial text (captures full paragraphs from 10-Ks)
- PDF: Embed pages directly when ≤6 pages; split into 6-page chunks for longer filings
- Audio: 60s segments balance context richness with the 120s API limit
- Images: One embedding per image — no chunking needed

### Search Behavior
- Default search uses full 3072-dim vectors for maximum quality
- Compact 768-dim toggle is exposed in the UI for latency comparison (useful for the book chapter discussion)
- Results are grouped by modality in the frontend, but ranked by a single similarity score

---

## 10. Dependencies Summary

### Backend (`pyproject.toml`)
```toml
[project]
name = "multimodal-financial-rag"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "google-genai>=1.0.0",
    "qdrant-client>=1.12.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "boto3>=1.35.0",
    "pydantic-settings>=2.6.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
]
```

### Frontend (`package.json` key deps)
```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "wavesurfer.js": "^7.8.0",
    "@react-pdf-viewer/core": "^3.12.0"
  }
}
```

---

## 11. Future Enhancements (Out of Scope for v1)

- **Interleaved embeddings:** Combine chart image + caption text in a single embedding for richer financial context
- **Streaming search:** WebSocket endpoint for real-time result updates as new documents are ingested
- **market-sentiment.io integration:** Wire search results into the existing regime detection dashboard as a "deep dive" panel
- **LLM-powered synthesis:** After retrieval, pass top-k results to an LLM (Claude or Gemini) for a synthesized answer with citations
- **Evaluation harness:** Build a retrieval quality benchmark using known-relevant document pairs across modalities
