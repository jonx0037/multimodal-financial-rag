"""Seed chart images: real price data rendered as candlestick/line charts."""

import argparse
import asyncio
import tempfile
from pathlib import Path

import httpx
import mplfinance as mpf
import yfinance as yf

CHARTS = [
    {
        "ticker": "AAPL",
        "title": "AAPL 6-Month Candlestick",
        "period": "6mo",
        "chart_type": "candle",
    },
    {
        "ticker": "NVDA",
        "title": "NVDA 6-Month Candlestick",
        "period": "6mo",
        "chart_type": "candle",
    },
    {
        "ticker": "MSFT",
        "title": "MSFT 3-Month Price & Volume",
        "period": "3mo",
        "chart_type": "candle",
    },
    {
        "ticker": "TSLA",
        "title": "TSLA 1-Year Price Trend",
        "period": "1y",
        "chart_type": "line",
    },
    {
        "ticker": "AMZN",
        "title": "AMZN 6-Month Candlestick",
        "period": "6mo",
        "chart_type": "candle",
    },
    {
        "ticker": "NVDA",
        "title": "NVDA 1-Year Price Trend",
        "period": "1y",
        "chart_type": "line",
    },
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
