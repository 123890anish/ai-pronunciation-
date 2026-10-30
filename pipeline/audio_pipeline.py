"""
Stage 1: Audio Ingestion and Preprocessing Pipeline.
Validates raw audio uploads, checks readability, and prepares normalized WAV for STT.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Optional, Tuple, Union

from audio.processor import normalize_audio_to_wav
from audio.recorder import save_uploaded_audio
from audio.validators import validate_audio_file
from llm.exceptions import AudioValidationError

logger = logging.getLogger("pronunciation_assessment.pipeline.audio")


@dataclass
class AudioPipelineResult:
    is_valid: bool
    saved_path: Optional[Path] = None
    normalized_path: Optional[Path] = None
    error_message: Optional[str] = None
    file_size_bytes: int = 0
    duration_seconds: Optional[float] = None


def process_incoming_audio(
    file_obj: Union[BinaryIO, Any],
    user_id: Union[int, str],
    filename: str,
    content_type: Optional[str] = None,
) -> AudioPipelineResult:
    """
    Stage 1 Execution:
    1. Validate size, extension, MIME type.
    2. Save recording securely in user's isolated media directory.
    3. Normalize audio format for speech recognition.
    """
    # Check basic validation
    is_valid, error = validate_audio_file(
        file_or_path=file_obj,
        filename=filename,
        content_type=content_type,
    )
    if not is_valid:
        logger.warning("Audio validation failed for user %s: %s", user_id, error)
        return AudioPipelineResult(
            is_valid=False,
            error_message=error or "Invalid audio file.",
        )

    try:
        saved_file_path = save_uploaded_audio(
            file_obj=file_obj,
            user_id=user_id,
            filename=filename,
        )
        file_size = saved_file_path.stat().st_size
    except Exception as exc:
        logger.error("Failed to save audio file to disk: %s", exc)
        return AudioPipelineResult(
            is_valid=False,
            error_message=f"Failed to store audio file securely: {exc}",
        )

    # Normalize to 16kHz WAV mono for high-fidelity speech recognition
    try:
        norm_path = normalize_audio_to_wav(saved_file_path)
    except Exception as exc:
        logger.warning("Audio normalization skipped (%s). Using original.", exc)
        norm_path = saved_file_path

    return AudioPipelineResult(
        is_valid=True,
        saved_path=saved_file_path,
        normalized_path=norm_path,
        file_size_bytes=file_size,
    )
