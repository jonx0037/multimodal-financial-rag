"""
Async SQLAlchemy wrapper for document and chunk CRUD operations.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.document import Base, Chunk, Document


class MetadataDB:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables(self) -> None:
        """Create tables if they don't exist (for development only — use Alembic in production)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def create_document(
        self,
        title: str,
        modality: str,
        source_type: str,
        storage_key: str,
        chunk_count: int = 0,
        ticker: str | None = None,
        published_at: str | datetime | None = None,
        file_size_bytes: int | None = None,
        extra_metadata: dict | None = None,
    ) -> str:
        """Insert a document record and return its ID."""
        if isinstance(published_at, str):
            published_at = datetime.fromisoformat(published_at)
        doc = Document(
            title=title,
            modality=modality,
            source_type=source_type,
            storage_key=storage_key,
            chunk_count=chunk_count,
            ticker=ticker,
            published_at=published_at,
            file_size_bytes=file_size_bytes,
            extra_metadata=extra_metadata or {},
        )
        async with self.session_factory() as session:
            session.add(doc)
            await session.commit()
            return str(doc.id)

    async def update_chunk_count(self, document_id: str, chunk_count: int) -> None:
        """Update the chunk count for a document."""
        async with self.session_factory() as session:
            doc = await session.get(Document, uuid.UUID(document_id))
            if doc:
                doc.chunk_count = chunk_count
                await session.commit()

    async def create_chunk(
        self,
        document_id: str,
        chunk_index: int,
        qdrant_point_id: str,
        text_preview: str | None = None,
        start_offset: int | None = None,
        end_offset: int | None = None,
    ) -> str:
        """Insert a chunk record and return its ID."""
        chunk = Chunk(
            document_id=uuid.UUID(document_id),
            chunk_index=chunk_index,
            qdrant_point_id=uuid.UUID(qdrant_point_id),
            text_preview=text_preview,
            start_offset=start_offset,
            end_offset=end_offset,
        )
        async with self.session_factory() as session:
            session.add(chunk)
            await session.commit()
            return str(chunk.id)

    async def get_document(self, document_id: str) -> Document | None:
        """Fetch a document by ID."""
        async with self.session_factory() as session:
            return await session.get(Document, uuid.UUID(document_id))

    async def get_chunks_by_document(self, document_id: str) -> list[Chunk]:
        """Fetch all chunks for a document, ordered by chunk_index."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Chunk)
                .where(Chunk.document_id == uuid.UUID(document_id))
                .order_by(Chunk.chunk_index)
            )
            return list(result.scalars().all())

    async def close(self) -> None:
        """Dispose the engine."""
        await self.engine.dispose()
