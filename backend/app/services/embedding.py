"""
Wraps the google-genai SDK for Gemini Embedding 2.
All calls use asyncio.to_thread() since the SDK is synchronous.
Includes exponential backoff for rate limit errors.
"""

import asyncio
import logging
from enum import Enum
from pathlib import Path

import google.genai as genai
from google.genai import types

logger = logging.getLogger(__name__)


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
    MODEL = "gemini-embedding-2-preview"
    DEFAULT_DIMS = 3072
    COMPACT_DIMS = 768
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # seconds

    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    async def _embed_with_retry(self, **kwargs) -> types.EmbedContentResponse:
        """Call embed_content with exponential backoff for rate limits."""
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await asyncio.to_thread(
                    self.client.models.embed_content, **kwargs
                )
                return result
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                delay = self.RETRY_DELAYS[attempt]
                logger.warning(
                    "Embedding request failed (attempt %d/%d): %s. Retrying in %ds...",
                    attempt + 1,
                    self.MAX_RETRIES,
                    e,
                    delay,
                )
                await asyncio.sleep(delay)
        raise RuntimeError("Unreachable")

    async def embed_text(
        self,
        texts: list[str],
        task_type: TaskType = TaskType.RETRIEVAL_DOCUMENT,
        dimensions: int = DEFAULT_DIMS,
    ) -> list[list[float]]:
        """Embed one or more text chunks. Supports batching."""
        result = await self._embed_with_retry(
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
        assert len(image_paths) <= 6, "Gemini supports max 6 images per request"
        parts = []
        for path in image_paths:
            img_bytes = path.read_bytes()
            mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
        result = await self._embed_with_retry(
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
        """Embed an audio segment (must be MP4, up to 120s). Native — no transcription."""
        audio_bytes = audio_path.read_bytes()
        result = await self._embed_with_retry(
            model=self.MODEL,
            contents=[types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp4")],
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
        """Embed a PDF directly (up to 6 pages)."""
        pdf_bytes = pdf_path.read_bytes()
        result = await self._embed_with_retry(
            model=self.MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
            ],
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
        result = await self._embed_with_retry(
            model=self.MODEL,
            contents=[query],
            config=types.EmbedContentConfig(
                task_type=TaskType.RETRIEVAL_QUERY.value,
                output_dimensionality=dimensions,
            ),
        )
        return result.embeddings[0].values
