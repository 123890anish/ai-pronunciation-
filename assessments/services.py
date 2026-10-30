"""
Assessments Application Services.
Encapsulates business operations between views, pipeline, and models.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from assessments.models import Assessment
from configure import get_config
from llm.model import check_ollama_health
from pipeline.assessment_pipeline import AssessmentOutput, run_assessment
from pipeline.history_pipeline import get_user_dashboard_stats

logger = logging.getLogger("pronunciation_assessment.assessments.services")


def process_user_audio_assessment(
    user: Any,
    audio_file: Any,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
) -> AssessmentOutput:
    """
    Submits uploaded user audio into the assessment pipeline.
    """
    return run_assessment(
        user=user,
        uploaded_audio=audio_file,
        original_filename=filename,
        content_type=content_type,
    )


def get_dashboard_context(user: Any) -> Dict[str, Any]:
    """Retrieve full dashboard context including metrics and system status."""
    stats = get_user_dashboard_stats(user)
    ollama_status = check_ollama_health()
    config = get_config()

    return {
        "stats": stats,
        "ollama_status": ollama_status,
        "config": config,
    }
