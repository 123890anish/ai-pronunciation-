"""
Audio Preprocessing and Format Normalization.
Converts input audio formats to 16kHz mono WAV suitable for Whisper or other STT models.
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("pronunciation_assessment.audio.processor")


def check_ffmpeg_installed() -> bool:
    """Check if ffmpeg binary is accessible in system PATH."""
    try:
        res = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return res.returncode == 0
    except Exception:
        return False


def normalize_audio_to_wav(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    target_sample_rate: int = 16000,
) -> Path:
    """
    Normalizes an audio recording to mono 16kHz WAV for optimal transcription.
    Uses ffmpeg CLI if available, or pydub if installed.
    If neither is available or conversion fails, returns the original input path safely.
    """
    in_p = Path(input_path).resolve()
    if not in_p.exists():
        raise FileNotFoundError(f"Input audio file not found: {in_p}")

    out_p = Path(output_path).resolve() if output_path else in_p.with_suffix(".norm.wav")

    # If it is already a WAV file and same path requested, return it
    if in_p.suffix.lower() == ".wav" and in_p == out_p:
        return in_p

    # Strategy 1: Try ffmpeg command line directly
    if check_ffmpeg_installed():
        try:
            cmd = [
                "ffmpeg",
                "-y",                    # overwrite output
                "-i", str(in_p),         # input file
                "-ar", str(target_sample_rate), # 16kHz
                "-ac", "1",              # mono
                "-c:a", "pcm_s16le",     # 16-bit PCM WAV
                str(out_p),
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            if res.returncode == 0 and out_p.exists() and out_p.stat().st_size > 0:
                logger.info("Successfully converted audio to %s using ffmpeg", out_p)
                return out_p
            logger.warning("ffmpeg failed: %s", res.stderr.decode(errors="ignore")[:200])
        except Exception as exc:
            logger.warning("ffmpeg execution failed: %s", exc)

    # Strategy 2: Try pydub if installed
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(str(in_p))
        seg = seg.set_frame_rate(target_sample_rate).set_channels(1)
        seg.export(str(out_p), format="wav")
        if out_p.exists() and out_p.stat().st_size > 0:
            logger.info("Successfully converted audio using pydub to %s", out_p)
            return out_p
    except Exception as exc:
        logger.debug("pydub conversion not available: %s", exc)

    # Fallback: return original file path
    logger.info("Using original audio file without normalization: %s", in_p)
    return in_p
