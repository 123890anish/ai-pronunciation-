"""
Stage 5: Assessment History & Learning Progress Analytics.
Calculates historical score trajectories and user dashboard metrics.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("pronunciation_assessment.pipeline.history")


def get_user_dashboard_stats(user: Any) -> Dict[str, Any]:
    """
    Computes dashboard analytics for authenticated user:
    - total_assessments
    - completed_count
    - average_grammar_score
    - latest_overall_score
    - recent_records
    - progress_chart_data
    """
    from assessments.models import Assessment
    from django.db.models import Avg

    user_qs = Assessment.objects.filter(user=user)
    total_assessments = user_qs.count()
    completed_qs = user_qs.filter(status="COMPLETED")
    completed_count = completed_qs.count()

    # Calculate average grammar score for completed assessments
    avg_grammar_agg = completed_qs.filter(grammar_score__isnull=False).aggregate(
        avg=Avg("grammar_score")
    )
    raw_avg = avg_grammar_agg.get("avg")
    average_grammar_score = round(float(raw_avg), 1) if raw_avg is not None else None

    # Latest assessment
    latest_record = user_qs.order_by("-created_at").first()
    latest_overall_score = (
        latest_record.overall_score
        if latest_record and latest_record.overall_score is not None
        else None
    )

    # Recent assessments for quick table
    recent_assessments = list(user_qs.order_by("-created_at")[:5])

    # Chart data: Last 10 completed assessments in chronological order
    chart_qs = list(completed_qs.order_by("-created_at")[:10])
    chart_qs.reverse()  # Oldest to newest for chronological line chart

    chart_labels = [rec.created_at.strftime("%b %d %H:%M") for rec in chart_qs]
    grammar_scores = [
        rec.grammar_score if rec.grammar_score is not None else 0.0
        for rec in chart_qs
    ]
    overall_scores = [
        rec.overall_score if rec.overall_score is not None else 0.0
        for rec in chart_qs
    ]

    return {
        "total_assessments": total_assessments,
        "completed_count": completed_count,
        "average_grammar_score": average_grammar_score,
        "latest_overall_score": latest_overall_score,
        "recent_assessments": recent_assessments,
        "chart_data": {
            "labels": chart_labels,
            "grammar_scores": grammar_scores,
            "overall_scores": overall_scores,
        },
    }
