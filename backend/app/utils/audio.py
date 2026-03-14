"""
Audio utilities: segmentation via ffmpeg and format conversion.
Uses asyncio.create_subprocess_exec for non-blocking ffmpeg calls.
Note: All ffmpeg calls use create_subprocess_exec (not shell=True) to prevent injection.
"""

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def convert_to_mp4(input_path: Path, output_path: Path | None = None) -> Path:
    """Convert any audio file to MP4 (AAC) format for Gemini compatibility."""
    if output_path is None:
        output_path = input_path.with_suffix(".mp4")

    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-i", str(input_path),
        "-c:a", "aac",
        "-y",
        str(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {stderr.decode()}")

    logger.info("Converted %s → %s", input_path.name, output_path.name)
    return output_path


async def segment_audio(
    input_path: Path,
    output_dir: Path,
    duration: int = 60,
    overlap: int = 10,
) -> list[Path]:
    """
    Split audio into overlapping segments using ffmpeg.

    Step size = duration - overlap (e.g., 60s segments with 10s overlap → 50s steps).
    Each segment is extracted as a separate MP4 file.
    """
    total_duration = await _get_duration(input_path)
    if total_duration is None:
        raise RuntimeError(f"Could not determine audio duration for {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    step = duration - overlap
    segments: list[Path] = []
    start = 0
    index = 0

    while start < total_duration:
        output_path = output_dir / f"seg_{index:03d}.mp4"
        process = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i", str(input_path),
            "-ss", str(start),
            "-t", str(duration),
            "-c:a", "aac",
            "-y",
            str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            logger.warning("ffmpeg segment %d failed: %s", index, stderr.decode()[:200])
            break

        segments.append(output_path)
        start += step
        index += 1

    logger.info(
        "Segmented %s into %d segments (%ds each, %ds overlap)",
        input_path.name, len(segments), duration, overlap,
    )
    return segments


async def _get_duration(audio_path: Path) -> float | None:
    """Get audio duration in seconds using ffprobe."""
    process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()
    try:
        return float(stdout.decode().strip())
    except (ValueError, AttributeError):
        return None
