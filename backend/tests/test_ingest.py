"""Tests for the ingestion pipeline."""

import pytest

from app.services.ingest import IngestionPipeline
from app.utils.chunking import chunk_text


class TestChunking:
    """Tests for the text chunking utility."""

    def test_single_chunk_short_text(self):
        result = chunk_text("a " * 100, window=512, overlap=128)
        assert len(result) == 1

    def test_multiple_chunks_with_overlap(self):
        result = chunk_text("word " * 1000, window=512, overlap=128)
        assert len(result) > 1

    def test_empty_text_returns_empty_list(self):
        result = chunk_text("")
        assert result == []

    def test_exact_window_size(self):
        result = chunk_text("w " * 512, window=512, overlap=128)
        assert len(result) == 1

    def test_overlap_content(self):
        words = [f"w{i}" for i in range(600)]
        text = " ".join(words)
        chunks = chunk_text(text, window=512, overlap=128)
        # Second chunk should start 384 words in (512 - 128)
        second_chunk_words = chunks[1].split()
        assert second_chunk_words[0] == "w384"


class TestIngestionPipeline:
    """Tests for the IngestionPipeline."""

    @pytest.mark.asyncio
    async def test_ingest_text_creates_chunks(
        self,
        mock_embedding_service,
        mock_vector_store,
        mock_metadata_db,
        mock_object_store,
    ):
        """Verify ingest_text chunks, embeds, upserts, and creates metadata."""
        pipeline = IngestionPipeline(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            metadata_db=mock_metadata_db,
            object_store=mock_object_store,
        )
        # 1000 words → should produce multiple chunks with default window=512, overlap=128
        text = "word " * 1000
        doc_id, chunk_count = await pipeline.ingest_text(
            text=text,
            title="Test Doc",
            source_type="news",
            ticker="AAPL",
        )

        assert chunk_count > 1
        # Should upload to S3
        mock_object_store.upload_file.assert_called_once()
        # Should batch embed — exactly 2 calls (3072 + 768)
        assert mock_embedding_service.embed_text.call_count == 2
        # Should upsert one point per chunk
        assert mock_vector_store.upsert.call_count == chunk_count
        # Should create one chunk record per chunk
        assert mock_metadata_db.create_chunk.call_count == chunk_count
        # Should update chunk count
        mock_metadata_db.update_chunk_count.assert_called_once_with(doc_id, chunk_count)

    @pytest.mark.asyncio
    async def test_ingest_image(
        self,
        mock_embedding_service,
        mock_vector_store,
        mock_metadata_db,
        mock_object_store,
        tmp_path,
    ):
        """Test image ingestion creates 1 chunk."""
        pipeline = IngestionPipeline(
            embedding_service=mock_embedding_service,
            vector_store=mock_vector_store,
            metadata_db=mock_metadata_db,
            object_store=mock_object_store,
        )

        # Create a fake image file
        img_bytes = b"\x89PNG\r\n" + b"\x00" * 100

        doc_id, chunk_count = await pipeline.ingest_image(
            image_bytes=img_bytes,
            filename="chart.png",
            title="AAPL Candlestick Q4",
            source_type="chart",
            ticker="AAPL",
        )

        assert chunk_count == 1
        mock_object_store.upload_file.assert_called_once()
        mock_vector_store.upsert.assert_called_once()
        mock_metadata_db.create_document.assert_called_once()
        mock_metadata_db.create_chunk.assert_called_once()

    @pytest.mark.asyncio
    async def test_split_pdf(self, tmp_path):
        """Test PDF splitting for long documents."""
        from pypdf import PdfWriter

        # Create a 15-page test PDF
        writer = PdfWriter()
        for _ in range(15):
            writer.add_blank_page(width=72, height=72)

        pdf_path = tmp_path / "test.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        sub_pdfs = IngestionPipeline._split_pdf(pdf_path, max_pages=6)
        assert len(sub_pdfs) == 3  # 6 + 6 + 3 pages
