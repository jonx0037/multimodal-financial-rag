"""
Qdrant adapter. Handles collection management, upsert, search, and filtering.
Uses AsyncQdrantClient for non-blocking operations.
"""

import logging
from datetime import datetime
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    DatetimeRange,
    FieldCondition,
    Filter,
    MatchValue,
    PayloadSchemaType,
    PointStruct,
)

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, url: str, api_key: str, collection: str = "financial_docs"):
        self.client = AsyncQdrantClient(url=url, api_key=api_key or None)
        self.collection = collection

    async def ensure_collection(self, vectors_config: dict) -> None:
        """Create the collection if it doesn't already exist."""
        exists = await self.client.collection_exists(self.collection)
        if exists:
            logger.info("Qdrant collection '%s' already exists", self.collection)
            return
        await self.client.create_collection(
            collection_name=self.collection,
            vectors_config=vectors_config,
        )
        logger.info("Created Qdrant collection '%s'", self.collection)

    async def ensure_payload_indexes(self) -> None:
        """Create payload indexes required for filtered search on Qdrant Cloud."""
        indexes = {
            "modality": PayloadSchemaType.KEYWORD,
            "ticker": PayloadSchemaType.KEYWORD,
            "source_type": PayloadSchemaType.KEYWORD,
            "date": PayloadSchemaType.DATETIME,
        }
        for field, schema_type in indexes.items():
            await self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field,
                field_schema=schema_type,
            )
        logger.info("Payload indexes ensured for collection '%s'", self.collection)

    async def upsert(
        self,
        full_vector: list[float],
        compact_vector: list[float],
        payload: dict,
    ) -> str:
        """Upsert a point with both full and compact named vectors."""
        point_id = str(uuid4())
        await self.client.upsert(
            collection_name=self.collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector={
                        "full": full_vector,
                        "compact": compact_vector,
                    },
                    payload=payload,
                )
            ],
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
        """Search with optional payload filtering by modality, ticker, and date range."""
        conditions = []
        if modality_filter:
            conditions.append(
                FieldCondition(key="modality", match=MatchValue(value=modality_filter))
            )
        if ticker_filter:
            conditions.append(
                FieldCondition(
                    key="ticker", match=MatchValue(value=ticker_filter.upper())
                )
            )
        if date_after or date_before:
            conditions.append(
                FieldCondition(
                    key="date",
                    range=DatetimeRange(
                        gte=datetime.fromisoformat(date_after) if date_after else None,
                        lte=datetime.fromisoformat(date_before)
                        if date_before
                        else None,
                    ),
                )
            )

        vector_name = "compact" if use_compact else "full"
        response = await self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            using=vector_name,
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
            for r in response.points
        ]

    async def close(self) -> None:
        """Close the async client."""
        await self.client.close()
