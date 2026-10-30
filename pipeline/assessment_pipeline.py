"""
Stage 3 & Orchestrator: Assessment Pipeline.
Coordinates audio processing, speech-to-text, grammar correction, feedback generation,
scoring, and database persistence.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Union

from configure import get_config
from llm.correction import correct_sentence
from llm.feedback import generate_feedback
from pipeline.audio_pipeline import process_incoming_audio
from pipeline.scoring_pipeline import ScoreResult, run_scoring_pipeline
from pipeline.transcription_pipeline import run_transcription_pipeline

logger = logging.getLogger("pronunciation_assessment.pipeline.assessment")


@dataclass
class AssessmentOutput:
    success: bool
    status: str  # 'COMPLETED' | 'FAILED' | 'PENDING' | 'PROCESSING'
    assessment_id: Optional[int] = None
    original_transcript: str = ""
    corrected_sentence: str = ""
    feedback: str = ""
    grammar_score: Optional[float] = None
    pronunciation_score: Optional[float] = None
    fluency_score: Optional[float] = None
    overall_score: Optional[float] = None
    audio_url: Optional[str] = None
    error_message: Optional[str] = None
    processing_duration: float = 0.0
    pronunciation_notice: Optional[str] = None
    fluency_notice: Optional[str] = None


def run_assessment(
    user: Any,
    uploaded_audio: Union[BinaryIO, Any],
    original_filename: Optional[str] = None,
    content_type: Optional[str] = None,
    stt_provider: Optional[str] = None,
    grammar_provider: Optional[str] = None,
) -> AssessmentOutput:
    """
    Main End-to-End Workflow Execution:
    1. Validate audio.
    2. Store recording securely.
    3. Initialize database record with PENDING / PROCESSING status.
    4. Transcribe audio via STT.
    5. Correct grammar via LLM / T5.
    6. Generate pedagogical feedback.
    7. Calculate transparent scores.
    8. Persist final results and return structured output.
    """
    start_time = time.time()
    filename = original_filename or getattr(uploaded_audio, "name", "recording.wav")
    user_id = getattr(user, "id", "anonymous")

    # Import Assessment model lazily to avoid circular imports during startup
    from assessments.models import Assessment

    # 1. Initialize DB record in PENDING state
    record = Assessment.objects.create(
        user=user,
        status="PENDING",
    )

    try:
        # Mark as PROCESSING
        record.status = "PROCESSING"
        record.save(update_fields=["status"])

        # Stage 1: Audio processing
        audio_res = process_incoming_audio(
            file_obj=uploaded_audio,
            user_id=user_id,
            filename=filename,
            content_type=content_type,
        )

        if not audio_res.is_valid or not audio_res.saved_path:
            error_msg = audio_res.error_message or "Audio file validation failed."
            record.status = "FAILED"
            record.error_message = error_msg
            record.save()
            return AssessmentOutput(
                success=False,
                status="FAILED",
                assessment_id=record.id,
                error_message=error_msg,
                processing_duration=round(time.time() - start_time, 2),
            )

        # Associate file with model
        config = get_config()
        media_root = Path(config.audio.media_root).resolve()
        rel_media_path = str(audio_res.saved_path.relative_to(media_root))
        record.audio_file.name = rel_media_path
        record.save(update_fields=["audio_file"])

        # Stage 2: Transcription
        transcription_target = audio_res.normalized_path or audio_res.saved_path
        stt_res = run_transcription_pipeline(
            audio_path=transcription_target,
            language=config.app.language,
            provider=stt_provider,
        )

        if not stt_res.success or not stt_res.transcript:
            error_msg = stt_res.error_message or "Speech recognition could not detect any audible speech."
            record.status = "FAILED"
            record.error_message = error_msg
            record.save(update_fields=["status", "error_message"])
            return AssessmentOutput(
                success=False,
                status="FAILED",
                assessment_id=record.id,
                error_message=error_msg,
                processing_duration=round(time.time() - start_time, 2),
            )

        original_transcript = stt_res.transcript
        record.original_transcript = original_transcript

        # Stage 3: Grammar Correction & Feedback
        correction_res = correct_sentence(
            text=original_transcript,
            provider=grammar_provider,
        )
        corrected_sentence = correction_res.get("corrected", original_transcript)
        record.corrected_sentence = corrected_sentence

        feedback_text = generate_feedback(
            original=original_transcript,
            corrected=corrected_sentence,
        )
        record.feedback = feedback_text

        # Stage 4: Scoring
        scoring_res: ScoreResult = run_scoring_pipeline(
            original_transcript=original_transcript,
            corrected_sentence=corrected_sentence,
            raw_pronunciation_score=None,  # Not claimed by STT alone
            raw_fluency_score=None,
        )

        record.grammar_score = scoring_res.grammar_score
        record.pronunciation_score = scoring_res.pronunciation_score
        record.fluency_score = scoring_res.fluency_score
        record.overall_score = scoring_res.overall_score

        # Finalize status & duration
        total_duration = round(time.time() - start_time, 2)
        record.status = "COMPLETED"
        record.processing_duration = total_duration
        record.error_message = ""
        record.save()

        return AssessmentOutput(
            success=True,
            status="COMPLETED",
            assessment_id=record.id,
            original_transcript=original_transcript,
            corrected_sentence=corrected_sentence,
            feedback=feedback_text,
            grammar_score=scoring_res.grammar_score,
            pronunciation_score=scoring_res.pronunciation_score,
            fluency_score=scoring_res.fluency_score,
            overall_score=scoring_res.overall_score,
            audio_url=record.audio_file.url if record.audio_file else None,
            processing_duration=total_duration,
            pronunciation_notice=scoring_res.pronunciation_notice,
            fluency_notice=scoring_res.fluency_notice,
        )

    except Exception as exc:
        logger.error("Unhandled exception during assessment pipeline: %s", exc, exc_info=True)
        record.status = "FAILED"
        record.error_message = (
            "Assessment processing failed unexpectedly. Please try again later."
        )
        record.processing_duration = round(time.time() - start_time, 2)
        record.save()

        return AssessmentOutput(
            success=False,
            status="FAILED",
            assessment_id=record.id,
            error_message=record.error_message,
            processing_duration=record.processing_duration,
        )
