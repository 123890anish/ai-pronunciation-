"""
Learner-focused Pedagogical Feedback Generator.
Generates concise, constructive explanations for ESL/EFL students.
"""
from __future__ import annotations

import logging
from typing import Optional

from common import normalize_text, strip_punctuation_lower
from configure import get_config
from llm.exceptions import LLMError
from llm.model import query_llm
from llm.prompts import PROMPT_LEARNER_FEEDBACK, SYSTEM_PROMPT_ENGLISH_TUTOR

logger = logging.getLogger("pronunciation_assessment.llm.feedback")


def _generate_rule_based_feedback(original: str, corrected: str) -> str:
    """Generate deterministic feedback when LLM is unavailable or offline."""
    orig_clean = strip_punctuation_lower(original)
    corr_clean = strip_punctuation_lower(corrected)

    if orig_clean == corr_clean:
        return (
            "• Excellent work! Your sentence structure and word order are natural and correct.\n"
            "• Keep practicing speaking fluently at a natural conversational pace."
        )

    orig_words = orig_clean.split()
    corr_words = corr_clean.split()

    feedback_points = []

    # Detect subject-verb or tense variations
    if len(orig_words) == len(corr_words):
        diffs = [
            f"'{o}' was refined to '{c}'"
            for o, c in zip(orig_words, corr_words)
            if o != c
        ]
        if diffs:
            feedback_points.append(f"• Word Choice / Grammar: {', '.join(diffs[:2])} for grammatical agreement.")
    elif len(orig_words) < len(corr_words):
        feedback_points.append("• Missing elements: Added necessary articles, prepositions, or auxiliary verbs to complete the clause.")
    else:
        feedback_points.append("• Concise phrasing: Removed redundant or unnecessary spoken fillers for clarity.")

    feedback_points.append("• Clear Meaning: The revised sentence sounds more natural to native English speakers.")
    feedback_points.append("• Tip: Repeat the corrected sentence aloud 3 times to build muscle memory!")

    return "\n".join(feedback_points)


def generate_feedback(original: str, corrected: str) -> str:
    """
    Generate pedagogical feedback explaining why corrections were made.

    Args:
        original: The transcribed user sentence.
        corrected: The grammatically corrected sentence.

    Returns:
        Structured learner-friendly feedback string.
    """
    orig_norm = normalize_text(original)
    corr_norm = normalize_text(corrected)

    if not orig_norm:
        return "No speech was detected to generate feedback."

    # If completely identical
    if strip_punctuation_lower(orig_norm) == strip_punctuation_lower(corr_norm):
        return (
            "• Perfect! Your sentence is grammatically accurate and natural.\n"
            "• No grammatical corrections were needed for this sentence."
        )

    config = get_config()
    if not config.assessment.feedback_enabled:
        return "Feedback is disabled in current application configuration."

    prompt = PROMPT_LEARNER_FEEDBACK.format(original=orig_norm, corrected=corr_norm)

    try:
        feedback_text = query_llm(
            prompt=prompt,
            system=SYSTEM_PROMPT_ENGLISH_TUTOR,
            temperature=0.2,
        )
        return feedback_text.strip()
    except (LLMError, Exception) as exc:
        logger.warning("Ollama feedback query failed (%s). Using rule-based fallback.", exc)
        return _generate_rule_based_feedback(orig_norm, corr_norm)
