"""
Grammar Correction Engine.
Supports Ollama LLM, HuggingFace T5-base-grammar-correction, and heuristic fallbacks.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

from common import normalize_text
from configure import get_config
from llm.exceptions import GrammarCorrectionError, LLMError
from llm.model import query_llm
from llm.prompts import PROMPT_GRAMMAR_CORRECTION, SYSTEM_PROMPT_ENGLISH_TUTOR

logger = logging.getLogger("pronunciation_assessment.llm.correction")

# Global cache for T5 pipeline to avoid reloading weights repeatedly
_T5_PIPELINE = None


def _load_t5_pipeline():
    """Lazily load T5 grammar correction pipeline if requested."""
    global _T5_PIPELINE
    if _T5_PIPELINE is not None:
        return _T5_PIPELINE
    try:
        from transformers import pipeline
        logger.info("Initializing HuggingFace T5 grammar correction model (vennify/t5-base-grammar-correction)...")
        _T5_PIPELINE = pipeline(
            "text2text-generation",
            model="vennify/t5-base-grammar-correction",
            tokenizer="vennify/t5-base-grammar-correction",
        )
        return _T5_PIPELINE
    except Exception as exc:
        logger.warning("Could not load T5 model: %s. Falling back to Ollama or rules.", exc)
        return None


def _correct_with_t5(text: str) -> Tuple[str, str]:
    """Correct sentence using T5 pipeline."""
    pipe = _load_t5_pipeline()
    if pipe is None:
        raise GrammarCorrectionError("T5 pipeline is unavailable or dependencies are not installed.")

    prompt_input = f"grammar: {text}"
    results = pipe(prompt_input, max_length=128, clean_up_tokenization_spaces=True)
    if results and isinstance(results, list):
        corrected = results[0].get("generated_text", "").strip()
        if not corrected:
            corrected = text
        explanation = "Sentence revised using T5 neural grammar correction model."
        return corrected, explanation
    return text, "Sentence verified as standard."


def _parse_json_from_llm_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """Attempt to parse structured JSON from model response."""
    # First try direct parse
    try:
        return json.loads(raw_text)
    except Exception:
        pass

    # Try extracting JSON markdown or curly brackets
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None


def _correct_with_ollama(text: str) -> Tuple[str, str]:
    """Correct sentence using Ollama local LLM."""
    prompt = PROMPT_GRAMMAR_CORRECTION.format(text=text)
    raw_response = query_llm(
        prompt=prompt,
        system=SYSTEM_PROMPT_ENGLISH_TUTOR,
        temperature=0.1,
    )

    parsed = _parse_json_from_llm_response(raw_response)
    if parsed and isinstance(parsed, dict) and "corrected" in parsed:
        corrected = normalize_text(parsed.get("corrected", text))
        explanation = parsed.get("explanation", "Grammar corrected by LLM tutor.")
        return corrected, explanation

    # If parsing failed, take the raw cleaned response
    cleaned = raw_response.strip().replace('"', "")
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if lines:
        return lines[0], "Corrected using LLM grammar analysis."
    return text, "No significant grammatical corrections required."


def _rule_based_fallback(text: str) -> Tuple[str, str]:
    """
    Lightweight heuristic fallback when offline/models are disabled.
    Handles basic capitalizations, punctuation, and common typos.
    """
    cleaned = normalize_text(text)
    if not cleaned:
        return "", "Empty input."

    # Capitalize first letter
    corrected = cleaned[0].upper() + cleaned[1:] if len(cleaned) > 1 else cleaned.upper()
    # Ensure terminal punctuation
    if not corrected.endswith((".", "!", "?")):
        corrected += "."

    # Common spoken transcription fixups
    replacements = [
        (r"\bi\b", "I"),
        (r"\bdont\b", "don't"),
        (r"\bcant\b", "can't"),
        (r"\bwont\b", "won't"),
        (r"\bim\b", "I'm"),
        (r"\bhe go\b", "he goes"),
        (r"\bshe go\b", "she goes"),
        (r"\bthey is\b", "they are"),
        (r"\bwe is\b", "we are"),
    ]
    for pattern, repl in replacements:
        corrected = re.sub(pattern, repl, corrected, flags=re.IGNORECASE)

    explanation = "Adjusted casing, capitalization, and standard punctuation."
    return corrected, explanation


def correct_sentence(text: str, provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Public API for sentence grammar correction.

    Args:
        text: Transcribed user speech or text input.
        provider: 'ollama' | 't5' | 'rule_based' (defaults to config)

    Returns:
        Dict containing:
            - 'original': str
            - 'corrected': str
            - 'explanation': str
            - 'status': 'SUCCESS' | 'NO_CHANGE' | 'FAILED'
            - 'provider_used': str
    """
    normalized_input = normalize_text(text)
    if not normalized_input:
        return {
            "original": "",
            "corrected": "",
            "explanation": "No speech or text provided for assessment.",
            "status": "FAILED",
            "provider_used": "none",
        }

    config = get_config()
    chosen_provider = provider or config.assessment.grammar_provider or "ollama"

    corrected = normalized_input
    explanation = ""
    status = "SUCCESS"
    provider_used = chosen_provider

    try:
        if chosen_provider == "t5":
            corrected, explanation = _correct_with_t5(normalized_input)
        elif chosen_provider == "ollama":
            try:
                corrected, explanation = _correct_with_ollama(normalized_input)
            except (LLMError, Exception) as llm_err:
                logger.warning("Ollama grammar correction failed (%s). Falling back to heuristic rules.", llm_err)
                corrected, explanation = _rule_based_fallback(normalized_input)
                provider_used = "fallback_rules"
                explanation += f" (Note: Ollama offline - {llm_err})"
        else:
            corrected, explanation = _rule_based_fallback(normalized_input)
            provider_used = "fallback_rules"

    except Exception as exc:
        logger.error("Grammar correction failed for '%s': %s", normalized_input, exc)
        corrected, explanation = _rule_based_fallback(normalized_input)
        provider_used = "fallback_emergency"
        status = "FAILED"
        explanation = f"Correction pipeline error: {exc}"

    if normalize_text(corrected).lower() == normalize_text(normalized_input).lower():
        status = "NO_CHANGE"
        if not explanation:
            explanation = "Your sentence is already grammatically natural and accurate!"

    return {
        "original": normalized_input,
        "corrected": normalize_text(corrected),
        "explanation": explanation,
        "status": status,
        "provider_used": provider_used,
    }
