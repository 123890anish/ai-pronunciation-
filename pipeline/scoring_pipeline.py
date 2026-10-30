"""
Stage 4: Scoring Pipeline.
Calculates transparent scores and enforces scoring integrity.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from configure import get_config
from llm.scoring import calculate_overall_score, compute_grammar_score

logger = logging.getLogger("pronunciation_assessment.pipeline.scoring")


@dataclass
class ScoreResult:
    grammar_score: Optional[float]
    pronunciation_score: Optional[float]
    fluency_score: Optional[float]
    overall_score: Optional[float]
    is_grammar_only: bool
    available_metrics: List[str]
    pronunciation_notice: Optional[str]
    fluency_notice: Optional[str]


def run_scoring_pipeline(
    original_transcript: str,
    corrected_sentence: str,
    raw_pronunciation_score: Optional[float] = None,
    raw_fluency_score: Optional[float] = None,
) -> ScoreResult:
    """
    Stage 4 Execution:
    - Calculates deterministic grammar score from transcript vs correction.
    - Resolves pronunciation & fluency metrics based on configured components.
    - Produces a transparent, weighted overall score.
    """
    config = get_config()

    # 1. Grammar score
    grammar_score: Optional[float] = None
    if config.assessment.grammar_correction_enabled:
        grammar_score = compute_grammar_score(original_transcript, corrected_sentence)

    # 2. Pronunciation score
    # Strictly check if phoneme-level acoustic assessment is enabled
    pronunciation_score: Optional[float] = None
    if config.assessment.pronunciation_scoring_enabled and raw_pronunciation_score is not None:
        pronunciation_score = max(0.0, min(100.0, float(raw_pronunciation_score)))

    # 3. Fluency score
    fluency_score: Optional[float] = None
    if config.assessment.fluency_scoring_enabled and raw_fluency_score is not None:
        fluency_score = max(0.0, min(100.0, float(raw_fluency_score)))

    # 4. Overall score
    score_data = calculate_overall_score(
        grammar_score=grammar_score,
        pronunciation_score=pronunciation_score,
        fluency_score=fluency_score,
    )

    return ScoreResult(
        grammar_score=score_data["grammar_score"],
        pronunciation_score=score_data["pronunciation_score"],
        fluency_score=score_data["fluency_score"],
        overall_score=score_data["overall_score"],
        is_grammar_only=score_data["is_grammar_only"],
        available_metrics=score_data["available_metrics"],
        pronunciation_notice=score_data["pronunciation_notice"],
        fluency_notice=score_data["fluency_notice"],
    )
