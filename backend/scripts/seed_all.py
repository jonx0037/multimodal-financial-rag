"""Run all seed scripts in sequence: text → charts → pdfs → audio."""

import argparse
import asyncio

from scripts.seed_audio import seed_audio
from scripts.seed_charts import seed_charts
from scripts.seed_pdfs import seed_pdfs
from scripts.seed_text import seed_text


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
