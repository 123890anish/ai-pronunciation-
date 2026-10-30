"""
Stage 2: Transcription Pipeline.
Runs Speech-to-Text inference and preserves verbatim original transcription.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from audio.speech_to_text import transcribe_audio
from common import normalize_text

logger = logging.getLogger("pronunciation_assessment.pipeline.transcription")


@dataclass
class TranscriptionResult:
    success: bool
    transcript: str
    detected_language: str = "en"
    provider: str = "whisper"
    error_message: Optional[str] = None


def run_transcription_pipeline(
    audio_path: Path,
    language: str = "en",
    provider: Optional[str] = None,
) -> TranscriptionResult:
    """
    Stage 2 Execution:
    Passes normalized audio through STT model, returning verbatim transcript.
    """
    if not audio_path.exists():
        return TranscriptionResult(
            success=False,
            transcript="",
            error_message=f"Audio file does not exist: {audio_path}",
        )

    stt_output = transcribe_audio(
        audio_path=audio_path,
        language=language,
        provider=provider,
    )

    status = stt_output.get("status")
    raw_text = stt_output.get("text", "")
    normalized_transcript = normalize_text(raw_text)

    if status == "SUCCESS" and normalized_transcript:
        return TranscriptionResult(
            success=True,
            transcript=normalized_transcript,
            detected_language=stt_output.get("language", language),
            provider=stt_output.get("provider", "whisper"),
        )

    # Empty audio or failure
    error = stt_output.get("error") or "No audible speech was recognized from the audio recording."
    logger.info("Speech transcription did not produce valid text: %s", error)

    return TranscriptionResult(
        success=False,
        transcript="",
        detected_language=stt_output.get("language", language),
        provider=stt_output.get("provider", "whisper"),
        error_message=error,
    )
