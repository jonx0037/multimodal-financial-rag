# Phase 3: Demo Data & Integration

## Approach
Hybrid data sourcing: real public data where authentic (SEC filings, stock prices), synthetic where practical (text reports, TTS audio).

## Scripts

All scripts live under `backend/scripts/`, POST to the FastAPI ingest endpoints via `httpx`.

### seed_text.py
- Hardcoded realistic financial text blobs (analyst notes, earnings summaries, sector outlooks)
- 5-8 documents across AAPL, NVDA, MSFT, TSLA, AMZN
- source_type: news
- No external data dependencies

### seed_audio.py
- Short earnings call scripts (~200 words each) per ticker
- Gemini TTS (`gemini-2.5-flash-preview-tts`) with different voices per speaker
- PCM → WAV → MP4 via ffmpeg
- 3-5 clips, source_type: earnings_call
- Requires GEMINI_API_KEY

### seed_charts.py
- `yfinance` for 6-month OHLCV data per ticker
- `mplfinance` candlestick charts, dark theme
- 5-8 PNG images, source_type: chart

### seed_pdfs.py
- Real SEC EDGAR 8-K and 10-Q PDFs (no auth, User-Agent header only)
- 4-6 filings, source_type: sec_filing

### seed_all.py
- Orchestrator: text → charts → pdfs → audio (audio last, slowest)
- All scripts target `http://localhost:8000`, configurable via `--api-url`

## Dependencies to add
httpx, yfinance, mplfinance, google-genai

## Target tickers
AAPL, NVDA, MSFT, TSLA, AMZN
