"""
Text chunking utilities for the ingestion pipeline.
Uses a sliding window approach for financial text.
"""

def chunk_text(text: str, window: int = 512, overlap: int = 128) -> list[str]:
    """Split text into overlapping word-based chunks for embedding.
    
    Uses word-level sliding window. For English financial text,
    1 word ≈ 1.3 Gemini tokens, so 512 words ≈ 665 tokens
    (well within the 8192-token embedding input limit).
    
    Args:
        text: Raw text to chunk.
        window: Number of words per chunk.
        overlap: Number of overlapping words between consecutive chunks.
    
    Returns:
        List of text chunks. Empty list if input is empty/whitespace.
    """
    words = text.split()
    if not words:
        return []

    step = window - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + window])
        chunks.append(chunk)
        if start + window >= len(words):
            break

    return chunks
