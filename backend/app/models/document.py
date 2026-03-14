"""
SQLAlchemy 2.0 async models for documents and chunks.
Maps to the PostgreSQL schema defined in the project brief (section 3.3).
"""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    modality: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # text | audio | pdf | image
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # earnings_call | sec_filing | news | chart
    ticker: Mapped[str | None] = mapped_column(String(10))
    published_at: Mapped[datetime | None] = mapped_column()
    ingested_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), default=datetime.utcnow
    )
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column()
    chunk_count: Mapped[int] = mapped_column(default=0)
    # 'metadata' is reserved by SQLAlchemy DeclarativeBase — use 'extra_metadata'
    extra_metadata: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), default=dict
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document {self.id} [{self.modality}] {self.title[:40]}>"


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE")
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    qdrant_point_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    text_preview: Mapped[str | None] = mapped_column(Text)
    start_offset: Mapped[int | None] = mapped_column()
    end_offset: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        server_default=text("NOW()"), default=datetime.utcnow
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk {self.id} doc={self.document_id} idx={self.chunk_index}>"
