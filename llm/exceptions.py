"""
Custom exceptions for the LLM and Assessment pipelines.
"""


class LLMError(Exception):
    """Base exception for all LLM-related failures."""
    pass


class OllamaConnectionError(LLMError):
    """Raised when unable to connect to the Ollama server."""
    pass


class OllamaTimeoutError(LLMError):
    """Raised when an Ollama request times out."""
    pass


class ModelResponseError(LLMError):
    """Raised when the LLM returns an empty, corrupted, or invalid payload."""
    pass


class GrammarCorrectionError(Exception):
    """Raised when grammar correction fails across all configured providers."""
    pass


class SpeechToTextError(Exception):
    """Raised when speech recognition fails."""
    pass


class AudioValidationError(Exception):
    """Raised when uploaded or recorded audio violates validation rules."""
    pass
