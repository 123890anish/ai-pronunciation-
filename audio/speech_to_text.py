"""
Interchangeable Speech-To-Text (STT) Service.
Supports OpenAI Whisper (local), Mock STT for unit tests, and custom pluggable providers.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

from configure import get_config
from llm.exceptions import SpeechToTextError

logger = logging.getLogger("pronunciation_assessment.audio.stt")

# Cached Whisper model
_WHISPER_MODEL_INSTANCE = None


def _load_whisper_model(model_name: str = "base"):
    """Lazily load local Whisper model."""
    global _WHISPER_MODEL_INSTANCE
    if _WHISPER_MODEL_INSTANCE is not None:
        return _WHISPER_MODEL_INSTANCE
    try:
        import whisper
        logger.info("Loading local Whisper model '%s'...", model_name)
        _WHISPER_MODEL_INSTANCE = whisper.load_model(model_name)
        return _WHISPER_MODEL_INSTANCE
    except ImportError as err:
        logger.error("openai-whisper package is not installed: %s", err)
        raise SpeechToTextError(
            "Whisper speech recognition library is not installed. "
            "Please run: pip install openai-whisper (and install ffmpeg)."
        ) from err
    except Exception as exc:
        logger.error("Failed to load Whisper model: %s", exc)
        raise SpeechToTextError(f"Error loading Whisper speech model: {exc}") from exc


def _transcribe_with_whisper(audio_path: Path, language: str = "en", model_name: str = "base") -> Dict[str, Any]:
    """Transcribe audio using local Whisper model."""
    model = _load_whisper_model(model_name)
    try:
        # Run transcription with fp16=False for universal CPU/GPU compatibility
        result = model.transcribe(
            str(audio_path),
            language=language if language != "auto" else None,
            fp16=False,
            temperature=0.0,
        )
        text = result.get("text", "").strip()
        detected_lang = result.get("language", language)
        return {
            "text": text,
            "language": detected_lang,
            "status": "SUCCESS" if text else "EMPTY",
            "error": None if text else "Audio contained no audible speech or was too quiet.",
        }
    except Exception as exc:
        logger.error("Whisper transcription failed on %s: %s", audio_path, exc)
        raise SpeechToTextError(f"Whisper inference error: {exc}") from exc


def _transcribe_with_mock(audio_path: Path, language: str = "en") -> Dict[str, Any]:
    """Mock STT implementation for automated tests and offline development."""
    return {
        "text": "Yesterday I go to market and bought three apple.",
        "language": language,
        "status": "SUCCESS",
        "error": None,
    }


def transcribe_audio(
    audio_path: Union[str, Path],
    language: str = "en",
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Primary interface for transcribing audio recordings into text.

    Args:
        audio_path: Absolute or relative path to the audio file.
        language: Expected spoken language ('en' by default).
        provider: 'whisper' | 'mock' (defaults to configure.yaml / .env).

    Returns:
        Structured dict:
            {
                "text": str,
                "language": str,
                "status": "SUCCESS" | "FAILED" | "EMPTY",
                "error": Optional[str],
                "provider": str
            }
    """
    path = Path(audio_path).resolve()
    if not path.exists():
        return {
            "text": "",
            "language": language,
            "status": "FAILED",
            "error": f"Audio file not found at {path}",
            "provider": provider or "unknown",
        }

    config = get_config()
    chosen_provider = (provider or config.assessment.stt_provider or "whisper").lower()

    if chosen_provider == "mock":
        res = _transcribe_with_mock(path, language)
        res["provider"] = "mock"
        return res

    # Default: Whisper STT
    try:
        res = _transcribe_with_whisper(
            audio_path=path,
            language=language,
            model_name=config.assessment.whisper_model,
        )
        res["provider"] = "whisper"
        return res
    except SpeechToTextError as stt_err:
        logger.warning("Whisper STT failed: %s", stt_err)
        return {
            "text": "",
            "language": language,
            "status": "FAILED",
            "error": str(stt_err),
            "provider": "whisper",
        }
    except Exception as exc:
        logger.error("Unexpected error during speech transcription: %s", exc)
        return {
            "text": "",
            "language": language,
            "status": "FAILED",
            "error": f"Speech-to-text failed: {exc}",
            "provider": "whisper",
        }
