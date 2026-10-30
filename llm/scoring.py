"""
Assessment Scoring Engine.
Computes deterministic and transparent scores for grammar, pronunciation, and fluency.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from common import calculate_word_similarity, normalize_text, strip_punctuation_lower
from configure import get_config

logger = logging.getLogger("pronunciation_assessment.llm.scoring")


def compute_grammar_score(original: str, corrected: str) -> float:
    """
    Computes a deterministic grammar accuracy score between 0.0 and 100.0.
    Based on word-level Levenshtein similarity between normalized spoken text
    and the grammatically corrected sentence.
    """
    orig_norm = normalize_text(original)
    corr_norm = normalize_text(corrected)

    if not orig_norm and not corr_norm:
        return 100.0
    if not orig_norm:
        return 0.0

    # If lowercase stripped versions match, score is 100
    if strip_punctuation_lower(orig_norm) == strip_punctuation_lower(corr_norm):
        return 100.0

    score = calculate_word_similarity(orig_norm, corr_norm)
    # Clamp strictly between 0 and 100
    return max(0.0, min(100.0, round(score, 1)))


def calculate_overall_score(
    grammar_score: Optional[float],
    pronunciation_score: Optional[float] = None,
    fluency_score: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes weighted overall score ONLY from enabled, available metrics.
    Ensures missing metrics are NOT treated as 0 or 100, but marked as unavailable.
    """
    config = get_config()

    total_weight = 0.0
    accumulated_points = 0.0
    available_metrics = []

    # 1. Grammar
    if config.assessment.grammar_correction_enabled and grammar_score is not None:
        weight = config.scoring.grammar_weight
        accumulated_points += grammar_score * weight
        total_weight += weight
        available_metrics.append("grammar")

    # 2. Pronunciation
    pronunciation_available = config.assessment.pronunciation_scoring_enabled and pronunciation_score is not None
    if pronunciation_available and pronunciation_score is not None:
        weight = config.scoring.pronunciation_weight
        accumulated_points += pronunciation_score * weight
        total_weight += weight
        available_metrics.append("pronunciation")

    # 3. Fluency
    fluency_available = config.assessment.fluency_scoring_enabled and fluency_score is not None
    if fluency_available and fluency_score is not None:
        weight = config.scoring.fluency_weight
        accumulated_points += fluency_score * weight
        total_weight += weight
        available_metrics.append("fluency")

    if total_weight > 0:
        overall = round(accumulated_points / total_weight, 1)
    else:
        overall = grammar_score if grammar_score is not None else 0.0

    pronunciation_notice = None
    if not pronunciation_available:
        pronunciation_notice = "Pronunciation score unavailable — phoneme-level assessment is not configured."

    fluency_notice = None
    if not fluency_available:
        fluency_notice = "Fluency score unavailable — acoustic pause/speech-rate model is not configured."

    return {
        "grammar_score": grammar_score,
        "pronunciation_score": pronunciation_score if pronunciation_available else None,
        "fluency_score": fluency_score if fluency_available else None,
        "overall_score": overall,
        "is_grammar_only": available_metrics == ["grammar"],
        "available_metrics": available_metrics,
        "pronunciation_notice": pronunciation_notice,
        "fluency_notice": fluency_notice,
    }
