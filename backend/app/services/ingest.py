"""
Ingestion pipeline: orchestrates file upload → chunking → embedding → vector upsert → metadata write.
Each modality has its own chunking strategy and embedding flow.
"""  # noqa: E501

import logging
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.services.embedding import EmbeddingService
from app.services.metadata import MetadataDB
from app.services.storage import ObjectStore
from app.services.vector_store import VectorStore
from app.utils.audio import convert_to_mp4, segment_audio
from app.utils.chunking import chunk_text

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        metadata_db: MetadataDB,
        object_store: ObjectStore,
    ):
        self.embed = embedding_service
        self.vectors = vector_store
        self.meta = metadata_db
        self.storage = object_store

    async def ingest_text(
        self,
        text: str,
        title: str,
        source_type: str,
        ticker: str | None = None,
        published_at: str | None = None,
        extra_metadata: dict | None = None,
    ) -> tuple[str, int]:
        """Ingest a text document: chunk → batch embed → upsert vectors + metadata."""
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Document produced no chunks after splitting.")

        # Upload raw file to object storage
        storage_key = f"text/{ticker or 'unknown'}/{title}.txt"
        await self.storage.upload_file(text.encode("utf-8"), storage_key, "text/plain")

        # Create document record (chunk_count updated after upserts)
        doc_id = await self.meta.create_document(
            title=title,
            modality="text",
            source_type=source_type,
            storage_key=storage_key,
            ticker=ticker,
            published_at=published_at,
            extra_metadata=extra_metadata,
        )

        # Batch embed — 2 API calls total regardless of chunk count
        full_vecs = await self.embed.embed_text(chunks, dimensions=3072)
        compact_vecs = await self.embed.embed_text(chunks, dimensions=768)

        # Upsert each chunk to Qdrant + PostgreSQL
        for i, (chunk, full_vec, compact_vec) in enumerate(
            zip(chunks, full_vecs, compact_vecs)
        ):
            point_id = await self.vectors.upsert(
                full_vector=full_vec,
                compact_vector=compact_vec,
                payload={
                    "modality": "text",
                    "source_type": source_type,
                    "ticker": ticker,
                    "date": published_at,
                    "chunk_index": i,
                    "parent_doc_id": doc_id,
                    "text_preview": chunk[:500],
                    "storage_key": storage_key,
                },
            )
            await self.meta.create_chunk(
                document_id=doc_id,
                chunk_index=i,
                qdrant_point_id=point_id,
                text_preview=chunk[:500],
                start_offset=i * (512 - 128),  # word offset, matches chunk_text step
            )

        await self.meta.update_chunk_count(doc_id, len(chunks))
        logger.info("Ingested text '%s': %d chunks", title, len(chunks))
        return doc_id, len(chunks)

    async def ingest_audio(
        self,
        audio_bytes: bytes,
        filename: str,
        title: str,
        source_type: str,
        ticker: str | None = None,
        published_at: str | None = None,
        extra_metadata: dict | None = None,
    ) -> tuple[str, int]:
        """Ingest audio: convert to MP4 → segment → embed each segment → upsert."""
        storage_key = f"audio/{filename}"
        await self.storage.upload_file(audio_bytes, storage_key, content_type="audio/mp4")

        doc_id = await self.meta.create_document(
            title=title,
            modality="audio",
            source_type=source_type,
            storage_key=storage_key,
            ticker=ticker,
            published_at=published_at,
            file_size_bytes=len(audio_bytes),
            extra_metadata=extra_metadata,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_path = tmpdir_path / filename
            input_path.write_bytes(audio_bytes)

            # Convert to MP4 if not already
            if input_path.suffix.lower() != ".mp4":
                input_path = await convert_to_mp4(input_path)

            # Segment into 60s chunks with 10s overlap
            segments = await segment_audio(
                input_path, tmpdir_path / "segments", duration=60, overlap=10
            )

            step = 50  # duration - overlap
            for i, seg_path in enumerate(segments):
                full_vec = await self.embed.embed_audio(seg_path, dimensions=3072)
                compact_vec = await self.embed.embed_audio(seg_path, dimensions=768)

                point_id = await self.vectors.upsert(
                    full_vector=full_vec,
                    compact_vector=compact_vec,
                    payload={
                        "modality": "audio",
                        "source_type": source_type,
                        "ticker": ticker,
                        "date": published_at,
                        "chunk_index": i,
                        "parent_doc_id": doc_id,
                        "text_preview": None,
                        "storage_key": storage_key,
                        "start_offset": i * step,
                    },
                )
                await self.meta.create_chunk(
                    document_id=doc_id,
                    chunk_index=i,
                    qdrant_point_id=point_id,
                    start_offset=i * step,
                    end_offset=i * step + 60,
                )

        chunk_count = len(segments)
        await self.meta.update_chunk_count(doc_id, chunk_count)
        logger.info("Ingested audio '%s': %d segments", title, chunk_count)
        return doc_id, chunk_count

    async def ingest_pdf(
        self,
        pdf_bytes: bytes,
        filename: str,
        title: str,
        source_type: str,
        ticker: str | None = None,
        published_at: str | None = None,
        extra_metadata: dict | None = None,
    ) -> tuple[str, int]:
        """Ingest PDF: split into ≤6-page chunks if needed → embed each chunk → upsert."""
        storage_key = f"pdfs/{filename}"
        await self.storage.upload_file(pdf_bytes, storage_key, content_type="application/pdf")

        doc_id = await self.meta.create_document(
            title=title,
            modality="pdf",
            source_type=source_type,
            storage_key=storage_key,
            ticker=ticker,
            published_at=published_at,
            file_size_bytes=len(pdf_bytes),
            extra_metadata=extra_metadata,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            pdf_path = tmpdir_path / filename
            pdf_path.write_bytes(pdf_bytes)

            # Split into ≤6-page sub-PDFs
            sub_pdfs = self._split_pdf(pdf_path, max_pages=6)

            for i, sub_path in enumerate(sub_pdfs):
                full_vec = await self.embed.embed_pdf(sub_path, dimensions=3072)
                compact_vec = await self.embed.embed_pdf(sub_path, dimensions=768)

                # Extract text preview from first page
                reader = PdfReader(str(sub_path))
                preview = (reader.pages[0].extract_text() or "")[:500]

                point_id = await self.vectors.upsert(
                    full_vector=full_vec,
                    compact_vector=compact_vec,
                    payload={
                        "modality": "pdf",
                        "source_type": source_type,
                        "ticker": ticker,
                        "date": published_at,
                        "chunk_index": i,
                        "parent_doc_id": doc_id,
                        "text_preview": preview,
                        "storage_key": storage_key,
                    },
                )
                await self.meta.create_chunk(
                    document_id=doc_id,
                    chunk_index=i,
                    qdrant_point_id=point_id,
                    text_preview=preview,
                    start_offset=i * 6,  # page offset
                )

        chunk_count = len(sub_pdfs)
        await self.meta.update_chunk_count(doc_id, chunk_count)
        logger.info("Ingested PDF '%s': %d chunks", title, chunk_count)
        return doc_id, chunk_count

    async def ingest_image(
        self,
        image_bytes: bytes,
        filename: str,
        title: str,
        source_type: str,
        ticker: str | None = None,
        published_at: str | None = None,
        extra_metadata: dict | None = None,
    ) -> tuple[str, int]:
        """Ingest a single image: embed → upsert. One embedding per image."""
        storage_key = f"images/{filename}"
        content_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
        await self.storage.upload_file(image_bytes, storage_key, content_type=content_type)

        doc_id = await self.meta.create_document(
            title=title,
            modality="image",
            source_type=source_type,
            storage_key=storage_key,
            ticker=ticker,
            published_at=published_at,
            file_size_bytes=len(image_bytes),
            extra_metadata=extra_metadata,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / filename
            img_path.write_bytes(image_bytes)

            full_vec = (await self.embed.embed_image([img_path], dimensions=3072))[0]
            compact_vec = (await self.embed.embed_image([img_path], dimensions=768))[0]

        point_id = await self.vectors.upsert(
            full_vector=full_vec,
            compact_vector=compact_vec,
            payload={
                "modality": "image",
                "source_type": source_type,
                "ticker": ticker,
                "date": published_at,
                "chunk_index": 0,
                "parent_doc_id": doc_id,
                "text_preview": None,
                "storage_key": storage_key,
            },
        )
        await self.meta.create_chunk(
            document_id=doc_id,
            chunk_index=0,
            qdrant_point_id=point_id,
        )
        await self.meta.update_chunk_count(doc_id, 1)
        logger.info("Ingested image '%s'", title)
        return doc_id, 1

    @staticmethod
    def _split_pdf(pdf_path: Path, max_pages: int = 6) -> list[Path]:
        """Split a PDF into sub-PDFs of at most `max_pages` pages each."""
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)

        if total_pages <= max_pages:
            return [pdf_path]

        sub_pdfs: list[Path] = []
        for start in range(0, total_pages, max_pages):
            writer = PdfWriter()
            for page_num in range(start, min(start + max_pages, total_pages)):
                writer.add_page(reader.pages[page_num])

            sub_path = pdf_path.parent / f"{pdf_path.stem}_chunk_{start // max_pages}.pdf"
            with open(sub_path, "wb") as f:
                writer.write(f)
            sub_pdfs.append(sub_path)

        return sub_pdfs
