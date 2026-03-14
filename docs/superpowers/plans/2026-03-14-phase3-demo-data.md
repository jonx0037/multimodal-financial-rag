# Phase 3: Demo Data & Integration — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate the multimodal RAG system with realistic demo data across all 4 modalities (text, audio, PDF, image) by creating seed scripts that POST to the running FastAPI ingest endpoints.

**Architecture:** Each script is standalone, uses `httpx` to POST multipart form data to the ingest API. Scripts are independent (can run individually) but `seed_all.py` orchestrates them in sequence. Text and charts are fully self-contained; PDFs download from SEC EDGAR; audio uses Gemini TTS.

**Tech Stack:** Python 3.11+, httpx (already a dep), yfinance + mplfinance (new), google-genai (already a dep), ffmpeg (already required for audio ingest)

---

## Chunk 1: Dependencies & Script Scaffolding

### Task 1: Add seed script dependencies to pyproject.toml

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add optional `seed` dependency group**

Add after the `dev` group in `pyproject.toml`:

```toml
seed = [
    "yfinance>=0.2.40",
    "mplfinance>=0.12.10",
]
```

Note: `httpx` and `google-genai` are already in the main dependencies.

- [ ] **Step 2: Install seed dependencies**

Run: `cd backend && uv pip install -e ".[seed]"`
Expected: All packages install successfully.

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml
git commit -m "chore: add seed script dependencies (yfinance, mplfinance)"
```

---

### Task 2: Create seed_text.py — synthetic analyst reports

**Files:**
- Create: `backend/scripts/seed_text.py`

- [ ] **Step 1: Create the script with document data and POST logic**

The script contains:
- A list of 8 hardcoded financial text documents (analyst notes, earnings summaries, sector outlooks)
- Each entry: `{"title", "text", "source_type", "ticker", "published_at"}`
- Tickers: AAPL, NVDA, MSFT, TSLA, AMZN
- source_type values: "news" for analyst notes, "earnings_call" for transcripts
- A `seed_text(api_url)` async function that POSTs each document to `/api/ingest/text`
- Uses `httpx.AsyncClient` with multipart form data: `data={"title": ..., "text": ..., "source_type": ..., "ticker": ..., "published_at": ...}`
- Prints progress: `[1/8] Ingested: AAPL Q4 2025 Earnings Summary (3 chunks)`
- CLI entrypoint with `--api-url` flag (default `http://localhost:8000`)

```python
"""Seed text documents: synthetic analyst reports and earnings summaries."""

import argparse
import asyncio

import httpx

DOCUMENTS = [
    {
        "title": "AAPL Q4 2025 Earnings Summary",
        "ticker": "AAPL",
        "source_type": "news",
        "published_at": "2025-10-30",
        "text": (
            "Apple Inc. reported fourth-quarter revenue of $94.9 billion, up 6% year over year, "
            "driven by record Services revenue of $25.0 billion and stronger-than-expected iPhone "
            "sales in Greater China. Gross margin expanded to 46.2%, reflecting favorable product "
            "mix and component cost tailwinds. Management guided Q1 FY2026 revenue between $124B "
            "and $128B, above consensus of $122B. The company announced a $110 billion share "
            "repurchase program and raised its quarterly dividend by 4% to $0.26 per share. "
            "CEO Tim Cook highlighted Apple Intelligence adoption, noting that Siri interactions "
            "increased 35% in markets where the feature launched. Services segment growth was "
            "fueled by advertising, App Store, and iCloud, offsetting moderate declines in "
            "Wearables. iPhone 16 Pro models saw above-plan demand, with titanium supply "
            "constraints easing by late September. Operating cash flow reached $27 billion for "
            "the quarter, bringing the trailing twelve-month figure to $118 billion. Capital "
            "expenditures were $3.2 billion, primarily for data center expansion to support "
            "on-device AI processing. Net income rose 12% to $24.7 billion, or $1.64 per diluted "
            "share, beating the Street estimate of $1.58. Apple's installed base crossed 2.3 "
            "billion active devices globally, a new record."
        ),
    },
    {
        "title": "NVDA FY2026 Q3 Earnings Analysis",
        "ticker": "NVDA",
        "source_type": "news",
        "published_at": "2025-11-20",
        "text": (
            "NVIDIA Corporation delivered another blowout quarter with revenue of $45.1 billion, "
            "up 94% year over year, as hyperscaler demand for Blackwell B200 and GB200 NVL72 "
            "systems continued to outpace supply. Data Center revenue accounted for $39.2 billion, "
            "with cloud service providers representing roughly 50% of data center sales. "
            "Management indicated that Blackwell production is ramping on schedule with TSMC's "
            "CoWoS-L packaging, and that demand visibility extends through FY2027. Gross margin "
            "was 73.5%, down from 75.1% in the prior quarter due to Blackwell ramp costs, but "
            "guided to recover above 75% as yields improve. Gaming revenue grew 15% to $3.8 "
            "billion, aided by the GeForce RTX 5090 launch. Jensen Huang reiterated NVIDIA's "
            "vision of sovereign AI infrastructure, noting new government partnerships in Saudi "
            "Arabia, India, and Japan. Networking revenue (InfiniBand + Spectrum-X) reached "
            "$4.1 billion, with Ethernet-based Spectrum-X growing 300% sequentially as customers "
            "deploy it alongside InfiniBand in large-scale clusters. Free cash flow was $21.8 "
            "billion. The company authorized an additional $50 billion in share buybacks."
        ),
    },
    {
        "title": "MSFT Azure Growth and AI Monetization",
        "ticker": "MSFT",
        "source_type": "news",
        "published_at": "2025-10-24",
        "text": (
            "Microsoft reported fiscal Q1 2026 revenue of $68.7 billion, up 16% year over year, "
            "with Intelligent Cloud segment revenue of $26.4 billion growing 22%. Azure and other "
            "cloud services revenue increased 34%, with AI services contributing 13 percentage "
            "points of that growth — up from 12 points last quarter. CEO Satya Nadella noted that "
            "Azure OpenAI Service now has over 70,000 customers, and GitHub Copilot subscribers "
            "surpassed 4 million. Microsoft 365 Copilot enterprise seats doubled sequentially. "
            "The Activision Blizzard acquisition contributed $2.8 billion in gaming revenue and "
            "is on track to be EPS accretive by Q3. Operating margin expanded 200 basis points "
            "to 45.8%, despite elevated capex of $14.9 billion for AI infrastructure. Management "
            "guided Q2 revenue of $70.5-71.5 billion and maintained full-year capex guidance of "
            "$58-62 billion, signaling sustained investment in AI training and inference capacity. "
            "LinkedIn revenue grew 9% with AI-powered features driving engagement. Dynamics 365 "
            "revenue grew 19%, with Copilot features in CRM and ERP increasing average deal size."
        ),
    },
    {
        "title": "TSLA Robotaxi Unveil and Q3 Delivery Miss",
        "ticker": "TSLA",
        "source_type": "news",
        "published_at": "2025-10-02",
        "text": (
            "Tesla delivered 435,000 vehicles in Q3 2025, missing consensus of 460,000, as the "
            "company prioritized Cybercab production line buildout at Giga Texas over Model Y "
            "output. Revenue was $25.2 billion, up 8% year over year but below the $26.1 billion "
            "estimate. The highlight was the October Robotaxi event at Warner Bros. Studios, where "
            "Elon Musk unveiled the production Cybercab design and demonstrated unsupervised FSD "
            "v13 in a controlled environment. Tesla guided for Cybercab production to begin in "
            "H2 2026 at a target COGS below $25,000. Automotive gross margin was 17.1%, down from "
            "18.9% last year due to price reductions across the lineup and ramp costs. Energy "
            "storage deployed 6.9 GWh, a sequential record. The Megapack factory in Lathrop "
            "reached a 40 GWh annualized run rate. Musk confirmed plans for a dedicated robotaxi "
            "network app and stated that Tesla aims for 1 million unsupervised FSD miles by year "
            "end. Regulatory approval timelines remain uncertain, with California and Texas as "
            "the priority markets."
        ),
    },
    {
        "title": "AMZN AWS Re-Acceleration and Retail Margins",
        "ticker": "AMZN",
        "source_type": "news",
        "published_at": "2025-10-31",
        "text": (
            "Amazon reported Q3 2025 revenue of $162.5 billion, up 11% year over year, with AWS "
            "revenue of $28.8 billion growing 19%, marking three consecutive quarters of "
            "re-acceleration. AWS operating margin hit 33%, up from 30% a year ago, as custom "
            "Trainium2 chips improved inference cost efficiency. CEO Andy Jassy highlighted that "
            "generative AI services on AWS now have a multi-billion dollar annualized revenue "
            "run rate, growing triple digits. North America operating margin reached 5.9%, the "
            "highest since 2018, driven by same-day delivery efficiencies and reduced last-mile "
            "costs. International segment turned profitable for the second consecutive quarter. "
            "Amazon announced Anthropic Claude integration as the default AI assistant across "
            "Alexa Plus, expanding the $10/month subscription launched in Q2. Advertising revenue "
            "grew 24% to $14.3 billion, with Prime Video ad-supported tier contributing. Capital "
            "expenditures were $21.2 billion, primarily for AWS infrastructure, with management "
            "guiding $75 billion full-year capex. Free cash flow was $47 billion on a trailing "
            "twelve-month basis."
        ),
    },
    {
        "title": "Semiconductor Sector Outlook Q4 2025",
        "ticker": None,
        "source_type": "news",
        "published_at": "2025-12-01",
        "text": (
            "The semiconductor industry enters Q4 2025 with bifurcated demand. AI-related chips "
            "(GPUs, HBM, custom ASICs) remain severely supply-constrained, with lead times for "
            "NVIDIA's Blackwell exceeding 40 weeks and SK Hynix HBM3e allocation sold out through "
            "2026. Meanwhile, traditional segments show mixed signals: automotive MCUs are "
            "recovering from a 12-month inventory correction, analog/mixed-signal faces mid-single "
            "digit declines, and industrial IoT remains soft. The SOX index is up 38% YTD, driven "
            "almost entirely by AI beneficiaries (NVDA +180%, AVGO +65%, MRVL +55%). Memory "
            "pricing has stabilized after the DRAM/NAND upcycle peaked in Q2, with Samsung and "
            "Micron guiding for low-single-digit sequential revenue growth. Key risks include "
            "potential US export restrictions on advanced AI chips to the Middle East, TSMC's "
            "Arizona fab yield challenges, and elevated inventory levels in the PC/smartphone "
            "supply chain. The SIA projects 2025 global semiconductor revenue of $685 billion, "
            "up 19% year over year, with AI accounting for roughly $120 billion of the total."
        ),
    },
    {
        "title": "AAPL Services Segment Deep Dive",
        "ticker": "AAPL",
        "source_type": "news",
        "published_at": "2025-11-15",
        "text": (
            "Apple's Services segment continues to be the crown jewel of the company's margin "
            "profile. In FY2025, Services revenue reached $96 billion, up 14% year over year, "
            "with gross margins exceeding 71%. The segment now accounts for 25% of total revenue "
            "but nearly 40% of gross profit. Key growth drivers include: (1) App Store — "
            "benefiting from the shift to in-app subscriptions, with 980 million paid subscribers "
            "across all platforms; (2) Advertising — search ads and News+ placements generating "
            "an estimated $9 billion annually; (3) Apple TV+ — crossing 50 million subscribers "
            "after winning multiple Emmy and Oscar awards; (4) iCloud+ — storage upgrades "
            "accelerating as on-device AI features require cloud sync for training data. "
            "The Google TAC payment ($20B/year for default search) remains a regulatory "
            "overhang following the DOJ antitrust ruling. If forced to compete on merits, Apple "
            "could lose $8-12B in annual high-margin revenue. However, management is building "
            "hedges through Apple Search expansion and the new Apple Intelligence API platform, "
            "which charges developers for on-device ML inference credits."
        ),
    },
    {
        "title": "Bearish Take: Overvaluation in Mega-Cap Tech",
        "ticker": None,
        "source_type": "news",
        "published_at": "2025-12-10",
        "text": (
            "The Magnificent Seven trade at an aggregate forward P/E of 32x, a 55% premium to "
            "the S&P 500 ex-tech at 20.5x. While earnings growth has justified elevated "
            "multiples — the group delivered 33% average EPS growth in 2025 — we see multiple "
            "risks converging in 2026. First, AI capex ROI scrutiny is intensifying: Microsoft, "
            "Google, Amazon, and Meta will collectively spend $240 billion on infrastructure in "
            "2025, but monetization is tracking well below investment pace. Second, regulatory "
            "headwinds are accelerating globally: the EU's Digital Markets Act penalties, the DOJ's "
            "Google search remedy, and potential FTC action against Amazon's marketplace practices. "
            "Third, the rate environment is less supportive than consensus expects — the Fed is "
            "likely to pause at 4.25% rather than cut further, keeping the equity risk premium "
            "compressed. Our framework suggests 15-20% downside for the group over 12 months if "
            "earnings growth decelerates to 15-18%, which is our base case as AI revenue fails to "
            "scale proportionally to capex. We recommend underweighting mega-cap tech in favor of "
            "mid-cap software names with cleaner AI monetization (DDOG, SNOW, CRWD)."
        ),
    },
]


async def seed_text(api_url: str) -> None:
    """POST each document to the text ingest endpoint."""
    async with httpx.AsyncClient(timeout=120) as client:
        for i, doc in enumerate(DOCUMENTS, 1):
            data = {
                "title": doc["title"],
                "text": doc["text"],
                "source_type": doc["source_type"],
            }
            if doc["ticker"]:
                data["ticker"] = doc["ticker"]
            if doc["published_at"]:
                data["published_at"] = doc["published_at"]

            resp = await client.post(f"{api_url}/api/ingest/text", data=data)
            resp.raise_for_status()
            result = resp.json()
            print(
                f"  [{i}/{len(DOCUMENTS)}] Ingested: {doc['title']} "
                f"({result['chunk_count']} chunks)"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed text documents")
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    print("=== Seeding text documents ===")
    asyncio.run(seed_text(args.api_url))
    print("Done.\n")
```

- [ ] **Step 2: Test the script manually**

Run (with backend + Docker services running):
```bash
cd backend && python -m scripts.seed_text
```
Expected: All 8 documents ingested, each printing chunk count.

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/seed_text.py
git commit -m "feat: add seed_text.py — 8 synthetic analyst reports"
```

---

### Task 3: Create seed_charts.py — stock chart images from yfinance

**Files:**
- Create: `backend/scripts/seed_charts.py`

- [ ] **Step 1: Create the script**

The script contains:
- A list of chart configs: `{"ticker", "title", "period", "chart_type"}`
- 6 charts: candlestick and line charts for various tickers and periods
- Uses `yfinance.download()` for OHLCV data
- Uses `mplfinance.plot()` with `style="nightclouds"` (dark theme) to render PNGs to a temp dir
- POSTs each PNG to `/api/ingest/image` as multipart file upload
- CLI entrypoint with `--api-url` flag

```python
"""Seed chart images: real price data rendered as candlestick/line charts."""

import argparse
import asyncio
import tempfile
from pathlib import Path

import httpx
import mplfinance as mpf
import yfinance as yf

CHARTS = [
    {"ticker": "AAPL", "title": "AAPL 6-Month Candlestick", "period": "6mo", "chart_type": "candle"},
    {"ticker": "NVDA", "title": "NVDA 6-Month Candlestick", "period": "6mo", "chart_type": "candle"},
    {"ticker": "MSFT", "title": "MSFT 3-Month Price & Volume", "period": "3mo", "chart_type": "candle"},
    {"ticker": "TSLA", "title": "TSLA 1-Year Price Trend", "period": "1y", "chart_type": "line"},
    {"ticker": "AMZN", "title": "AMZN 6-Month Candlestick", "period": "6mo", "chart_type": "candle"},
    {"ticker": "NVDA", "title": "NVDA 1-Year Price Trend", "period": "1y", "chart_type": "line"},
]


def render_chart(ticker: str, period: str, chart_type: str, output_path: Path) -> None:
    """Download price data and render a chart to PNG."""
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    # Flatten multi-level columns if present (yfinance 0.2.40+)
    if hasattr(df.columns, "levels") and len(df.columns.levels) > 1:
        df.columns = df.columns.get_level_values(0)
    mpf.plot(
        df,
        type=chart_type,
        style="nightclouds",
        title=f"{ticker} ({period})",
        volume=True,
        savefig=dict(fname=str(output_path), dpi=150, bbox_inches="tight"),
    )


async def seed_charts(api_url: str) -> None:
    """Render charts and POST each to the image ingest endpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        async with httpx.AsyncClient(timeout=120) as client:
            for i, chart in enumerate(CHARTS, 1):
                filename = f"{chart['ticker']}_{chart['period']}_{chart['chart_type']}.png"
                output_path = Path(tmpdir) / filename

                render_chart(
                    chart["ticker"], chart["period"], chart["chart_type"], output_path
                )

                with open(output_path, "rb") as f:
                    resp = await client.post(
                        f"{api_url}/api/ingest/image",
                        data={
                            "title": chart["title"],
                            "source_type": "chart",
                            "ticker": chart["ticker"],
                        },
                        files={"file": (filename, f, "image/png")},
                    )
                resp.raise_for_status()
                result = resp.json()
                print(
                    f"  [{i}/{len(CHARTS)}] Ingested: {chart['title']} "
                    f"({result['chunk_count']} chunks)"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed chart images")
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    print("=== Seeding chart images ===")
    asyncio.run(seed_charts(args.api_url))
    print("Done.\n")
```

- [ ] **Step 2: Test manually**

Run: `cd backend && python -m scripts.seed_charts`
Expected: 6 charts rendered and ingested, each printing 1 chunk.

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/seed_charts.py
git commit -m "feat: add seed_charts.py — yfinance candlestick/line charts"
```

---

## Chunk 2: PDF and Audio Seeds

### Task 4: Create seed_pdfs.py — real SEC EDGAR filings

**Files:**
- Create: `backend/scripts/seed_pdfs.py`

- [ ] **Step 1: Create the script**

The script contains:
- A list of real SEC EDGAR filing URLs (direct PDF links from EDGAR full-text search)
- 5 filings: mix of 8-K and 10-Q across the target tickers
- Downloads each PDF with a proper User-Agent header (SEC requires it)
- POSTs each to `/api/ingest/pdf` as multipart file upload
- CLI entrypoint with `--api-url` flag

```python
"""Seed PDF documents: real SEC EDGAR 8-K and 10-Q filings."""

import argparse
import asyncio

import httpx

# Real SEC EDGAR filing URLs — these are stable, public, direct-PDF links.
# User-Agent is required by SEC EDGAR fair access policy.
EDGAR_USER_AGENT = "MultimodalRAG/1.0 (demo@datasalt.ai)"

FILINGS = [
    {
        "title": "AAPL 10-Q FY2025 Q3",
        "ticker": "AAPL",
        "source_type": "sec_filing",
        "published_at": "2025-08-01",
        "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000077/aapl-20250628.htm",
        "filename": "aapl_10q_2025q3.pdf",
    },
    {
        "title": "NVDA 10-Q FY2026 Q1",
        "ticker": "NVDA",
        "source_type": "sec_filing",
        "published_at": "2025-05-28",
        "url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581025000065/nvda-20250427.htm",
        "filename": "nvda_10q_2026q1.pdf",
    },
    {
        "title": "MSFT 8-K FY2025 Q4 Earnings",
        "ticker": "MSFT",
        "source_type": "sec_filing",
        "published_at": "2025-07-22",
        "url": "https://www.sec.gov/Archives/edgar/data/789019/000119312525162222/d864929d8k.htm",
        "filename": "msft_8k_2025q4.pdf",
    },
    {
        "title": "TSLA 10-Q 2025 Q2",
        "ticker": "TSLA",
        "source_type": "sec_filing",
        "published_at": "2025-07-23",
        "url": "https://www.sec.gov/Archives/edgar/data/1318605/000162828025033393/tsla-20250630.htm",
        "filename": "tsla_10q_2025q2.pdf",
    },
    {
        "title": "AMZN 8-K 2025 Q2 Earnings",
        "ticker": "AMZN",
        "source_type": "sec_filing",
        "published_at": "2025-08-01",
        "url": "https://www.sec.gov/Archives/edgar/data/1018724/000101872425000040/amzn-20250801.htm",
        "filename": "amzn_8k_2025q2.pdf",
    },
]


async def download_filing(url: str, client: httpx.AsyncClient) -> bytes:
    """Download a filing from SEC EDGAR with required User-Agent."""
    resp = await client.get(url, headers={"User-Agent": EDGAR_USER_AGENT})
    resp.raise_for_status()
    return resp.content


async def seed_pdfs(api_url: str) -> None:
    """Download filings from EDGAR and POST each to the PDF ingest endpoint."""
    async with httpx.AsyncClient(timeout=180, follow_redirects=True) as client:
        for i, filing in enumerate(FILINGS, 1):
            print(f"  [{i}/{len(FILINGS)}] Downloading: {filing['title']}...")
            try:
                pdf_bytes = await download_filing(filing["url"], client)
            except httpx.HTTPStatusError as e:
                print(f"    SKIP — download failed: {e.response.status_code}")
                continue

            resp = await client.post(
                f"{api_url}/api/ingest/pdf",
                data={
                    "title": filing["title"],
                    "source_type": filing["source_type"],
                    "ticker": filing["ticker"],
                    "published_at": filing["published_at"],
                },
                files={"file": (filing["filename"], pdf_bytes, "application/pdf")},
            )
            resp.raise_for_status()
            result = resp.json()
            print(
                f"    Ingested: {filing['title']} "
                f"({result['chunk_count']} chunks, {len(pdf_bytes) // 1024}KB)"
            )

            # Respect SEC rate limit: 10 requests per second max
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed PDF documents from SEC EDGAR")
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    print("=== Seeding PDF documents ===")
    asyncio.run(seed_pdfs(args.api_url))
    print("Done.\n")
```

**Note:** The EDGAR URLs above are illustrative. During implementation, verify the actual URLs are valid by checking EDGAR. If any return 404, find the correct filing URL for that company/period from `https://efts.sec.gov/LATEST/search-index?q=...` or the EDGAR company search page.

- [ ] **Step 2: Test manually**

Run: `cd backend && python -m scripts.seed_pdfs`
Expected: 5 PDFs downloaded and ingested (some may have multiple chunks if >6 pages).

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/seed_pdfs.py
git commit -m "feat: add seed_pdfs.py — SEC EDGAR 8-K and 10-Q filings"
```

---

### Task 5: Create seed_audio.py — Gemini TTS earnings call clips

**Files:**
- Create: `backend/scripts/seed_audio.py`

- [ ] **Step 1: Create the script**

The script contains:
- 4 earnings call scripts (~200 words each, written as CEO/CFO quotes)
- Uses `google.genai` Client with `gemini-2.5-flash-preview-tts`
- Different voices per company (Kore, Charon, Orus, Fenrir)
- Generates PCM → saves as WAV → converts to MP4 via ffmpeg subprocess
- POSTs each MP4 to `/api/ingest/audio` as multipart file upload
- Requires `GEMINI_API_KEY` env var
- CLI entrypoint with `--api-url` flag

**USER CONTRIBUTION POINT:** The `generate_earnings_audio()` function is where you shape the TTS call and voice assignment. This is the core creative decision — mapping voices to companies and crafting the prompt that controls delivery style.

```python
"""Seed audio documents: Gemini TTS earnings call clips."""

import argparse
import asyncio
import os
import subprocess
import tempfile
import wave
from pathlib import Path

import httpx
from google import genai
from google.genai import types

EARNINGS_SCRIPTS = [
    {
        "title": "AAPL Q4 2025 Earnings Call — CEO Remarks",
        "ticker": "AAPL",
        "source_type": "earnings_call",
        "published_at": "2025-10-30",
        "voice": "Kore",
        "prompt": (
            "Speak in a calm, confident, executive tone as if delivering an earnings call: "
            "Good afternoon, and thank you for joining us. We are pleased to report our strongest "
            "fourth quarter ever, with revenue of ninety-four point nine billion dollars. iPhone "
            "sales exceeded our expectations across all geographies, and our Services segment "
            "reached a new all-time revenue record. We are particularly excited about the early "
            "adoption of Apple Intelligence features, which are driving increased engagement "
            "across our ecosystem. Looking ahead, we see tremendous opportunity in health, "
            "spatial computing, and AI-powered experiences."
        ),
    },
    {
        "title": "NVDA FY2026 Q3 Earnings Call — CEO Remarks",
        "ticker": "NVDA",
        "source_type": "earnings_call",
        "published_at": "2025-11-20",
        "voice": "Charon",
        "prompt": (
            "Speak with energy and enthusiasm as a tech CEO delivering blockbuster earnings: "
            "The age of AI is here, and NVIDIA is at the center of it. We delivered forty-five "
            "point one billion in revenue this quarter, nearly doubling year over year. Blackwell "
            "demand is incredible — every major cloud provider, every sovereign nation building "
            "AI infrastructure, they all need our platform. Our networking business is also "
            "inflecting as Spectrum-X Ethernet gains traction alongside InfiniBand. The next "
            "wave of AI will move from training to inference, and our full-stack platform is "
            "uniquely positioned to capture that transition."
        ),
    },
    {
        "title": "MSFT FQ1 2026 Earnings Call — CEO Remarks",
        "ticker": "MSFT",
        "source_type": "earnings_call",
        "published_at": "2025-10-24",
        "voice": "Orus",
        "prompt": (
            "Speak in a measured, thoughtful, executive tone for an earnings call: "
            "Thank you everyone. This was an outstanding quarter for Microsoft. Azure revenue "
            "grew thirty-four percent, with AI services now contributing thirteen points of that "
            "growth. GitHub Copilot has surpassed four million subscribers, and Microsoft 365 "
            "Copilot enterprise adoption doubled. We are seeing the real-world impact of AI "
            "across every workload — from code generation to customer service to data analytics. "
            "Our capital investments reflect our conviction that this is a generational platform "
            "shift, and we are building the infrastructure to lead it."
        ),
    },
    {
        "title": "AMZN Q3 2025 Earnings Call — CEO Remarks",
        "ticker": "AMZN",
        "source_type": "earnings_call",
        "published_at": "2025-10-31",
        "voice": "Fenrir",
        "prompt": (
            "Speak in a direct, business-focused executive tone for an earnings call: "
            "Good evening. AWS re-accelerated to nineteen percent growth this quarter, and our "
            "generative AI services are now at a multi-billion dollar run rate growing triple "
            "digits. We are seeing strong demand for Trainium custom silicon, which significantly "
            "improves inference cost efficiency for our customers. On the retail side, our "
            "same-day delivery network is driving higher order frequency and improving margins. "
            "North America operating margin reached five point nine percent, our highest since "
            "twenty eighteen. We remain focused on long-term customer obsession."
        ),
    },
]


def pcm_to_wav(pcm_data: bytes, output_path: Path) -> None:
    """Write raw PCM data (24kHz, 16-bit, mono) to a WAV file."""
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm_data)


def wav_to_mp4(wav_path: Path, mp4_path: Path) -> None:
    """Convert WAV to MP4/AAC using ffmpeg."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(wav_path),
            "-c:a", "aac", "-b:a", "128k",
            str(mp4_path),
        ],
        capture_output=True,
        check=True,
    )


async def generate_earnings_audio(
    script: dict, client: genai.Client, tmpdir: Path
) -> Path:
    """Generate TTS audio for an earnings call script. Returns path to MP4 file.

    This is the function where the TTS call and voice assignment happen.
    The prompt in each script controls delivery style (calm, energetic, etc.)
    and the voice name selects the speaker timbre.
    """
    # TODO: Jonathan — implement the Gemini TTS call here.
    # Use client.models.generate_content() with:
    #   - model="gemini-2.5-flash-preview-tts"
    #   - contents=script["prompt"]
    #   - config with response_modalities=["AUDIO"] and speech_config using script["voice"]
    # Extract PCM data from response.candidates[0].content.parts[0].inline_data.data
    # Then convert PCM → WAV → MP4 and return the MP4 path.
    raise NotImplementedError("Implement the TTS generation logic")


async def seed_audio(api_url: str) -> None:
    """Generate TTS audio and POST each to the audio ingest endpoint."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set. Skipping audio seed.")
        return

    tts_client = genai.Client(api_key=api_key)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        async with httpx.AsyncClient(timeout=300) as http_client:
            for i, script in enumerate(EARNINGS_SCRIPTS, 1):
                print(f"  [{i}/{len(EARNINGS_SCRIPTS)}] Generating: {script['title']}...")
                mp4_path = await generate_earnings_audio(script, tts_client, tmpdir_path)

                with open(mp4_path, "rb") as f:
                    resp = await http_client.post(
                        f"{api_url}/api/ingest/audio",
                        data={
                            "title": script["title"],
                            "source_type": script["source_type"],
                            "ticker": script["ticker"],
                            "published_at": script["published_at"],
                        },
                        files={"file": (mp4_path.name, f, "audio/mp4")},
                    )
                resp.raise_for_status()
                result = resp.json()
                print(
                    f"    Ingested: {script['title']} "
                    f"({result['chunk_count']} segments)"
                )

                # Rate limit: Gemini free tier
                await asyncio.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed audio documents via Gemini TTS")
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    print("=== Seeding audio documents ===")
    asyncio.run(seed_audio(args.api_url))
    print("Done.\n")
```

- [ ] **Step 2: Jonathan implements `generate_earnings_audio()`**

See the TODO in the function. This is the creative decision point — mapping the Gemini TTS API to the earnings call scripts.

Guidance:
- Use `client.models.generate_content()` (sync, will be called from async context via `asyncio.to_thread`)
- The `speech_config` nesting is: `SpeechConfig` → `VoiceConfig` → `PrebuiltVoiceConfig(voice_name=...)`
- PCM output is 24kHz 16-bit mono — use the `pcm_to_wav` helper, then `wav_to_mp4`
- Return the final MP4 path

- [ ] **Step 3: Test manually**

Run: `cd backend && python -m scripts.seed_audio`
Expected: 4 audio clips generated and ingested, each showing segment count.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/seed_audio.py
git commit -m "feat: add seed_audio.py — Gemini TTS earnings call clips"
```

---

## Chunk 3: Orchestrator & Integration

### Task 6: Create seed_all.py — orchestrator script

**Files:**
- Create: `backend/scripts/seed_all.py`
- Create: `backend/scripts/__init__.py`

- [ ] **Step 1: Create `__init__.py` for the scripts package**

Empty file to enable `python -m scripts.*` imports.

```python
```

- [ ] **Step 2: Create `seed_all.py`**

```python
"""Run all seed scripts in sequence: text → charts → pdfs → audio."""

import argparse
import asyncio

from scripts.seed_text import seed_text
from scripts.seed_charts import seed_charts
from scripts.seed_pdfs import seed_pdfs
from scripts.seed_audio import seed_audio


async def seed_all(api_url: str) -> None:
    print("=" * 50)
    print("Multimodal Financial RAG — Demo Data Seeder")
    print("=" * 50)
    print(f"Target API: {api_url}\n")

    print("=== Phase 1: Text Documents ===")
    await seed_text(api_url)

    print("=== Phase 2: Chart Images ===")
    await seed_charts(api_url)

    print("=== Phase 3: PDF Filings ===")
    await seed_pdfs(api_url)

    print("=== Phase 4: Audio Clips (slowest) ===")
    await seed_audio(api_url)

    print("=" * 50)
    print("All demo data seeded successfully!")
    print("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed all demo data")
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    asyncio.run(seed_all(args.api_url))
```

- [ ] **Step 3: Test the orchestrator**

Run: `cd backend && python -m scripts.seed_all`
Expected: All 4 phases run in sequence, ~23 total documents ingested.

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/__init__.py backend/scripts/seed_all.py
git commit -m "feat: add seed_all.py orchestrator for all demo data"
```

---

### Task 7: Verify end-to-end search across all modalities

- [ ] **Step 1: Test multimodal search via curl**

```bash
# Search for AI-related content across all modalities
curl -s http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "AI infrastructure investment", "limit": 10}' | python -m json.tool

# Filter by modality
curl -s http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "earnings revenue growth", "modalities": ["text", "audio"], "limit": 5}' | python -m json.tool

# Filter by ticker
curl -s http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "quarterly results", "tickers": ["NVDA"], "limit": 5}' | python -m json.tool
```

Expected: Results from multiple modalities with scores, text_preview where applicable, and valid storage_key URLs.

- [ ] **Step 2: Test via frontend**

Open `http://localhost:3000`, search "NVIDIA earnings", verify:
- Text results show analyst reports
- Image results show NVDA charts
- PDF results show SEC filings
- Audio results show earnings call clips (if audio player works)

- [ ] **Step 3: Commit any fixes**

- [ ] **Step 4: Update project status memory**

Update `memory/project_status.md` to mark Phase 3 as COMPLETE.
