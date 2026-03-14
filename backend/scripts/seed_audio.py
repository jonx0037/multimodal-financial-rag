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
from google.genai import types  # noqa: F401 — needed for generate_earnings_audio

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
    client,
    script: dict,
    output_dir: Path,
) -> Path:
    """Generate earnings call audio via Gemini TTS and convert to MP4."""
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-preview-tts",
        contents=script["prompt"],
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=script["voice"],
                    )
                )
            ),
        ),
    )

    pcm_data = response.candidates[0].content.parts[0].inline_data.data
    wav_path = output_dir / f"{script['ticker']}_earnings.wav"
    mp4_path = output_dir / f"{script['ticker']}_earnings.mp4"

    pcm_to_wav(pcm_data, wav_path)
    wav_to_mp4(wav_path, mp4_path)

    return mp4_path


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
                mp4_path = await generate_earnings_audio(tts_client, script, tmpdir_path)

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
