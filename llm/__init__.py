"""
LLM Module for Pronunciation & Grammar Assessment.
Exposes query_llm, correct_sentence, generate_feedback, and compute_grammar_score.
"""
from llm.correction import correct_sentence
from llm.exceptions import (
    AudioValidationError,
    GrammarCorrectionError,
    LLMError,
    ModelResponseError,
    OllamaConnectionError,
    OllamaTimeoutError,
    SpeechToTextError,
)
from llm.feedback import generate_feedback
from llm.model import OLLAMA_MODEL, OLLAMA_TIMEOUT, OLLAMA_URL, check_ollama_health, query_llm
from llm.scoring import calculate_overall_score, compute_grammar_score

__all__ = [
    "query_llm",
    "correct_sentence",
    "generate_feedback",
    "compute_grammar_score",
    "calculate_overall_score",
    "check_ollama_health",
    "OLLAMA_URL",
    "OLLAMA_MODEL",
    "OLLAMA_TIMEOUT",
    "LLMError",
    "OllamaConnectionError",
    "OllamaTimeoutError",
    "ModelResponseError",
    "GrammarCorrectionError",
    "SpeechToTextError",
    "AudioValidationError",
]
