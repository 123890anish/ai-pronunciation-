"""
Assessment Data Models.
Tracks user recordings, transcripts, LLM grammar corrections, feedback, and scores.
"""
import os
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


def user_audio_upload_path(instance, filename):
    """Dynamically partition recordings by user id and date."""
    user_id = instance.user_id if instance.user_id else "anonymous"
    return f"recordings/user_{user_id}/{filename}"


class Assessment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assessments",
        db_index=True,
    )
    audio_file = models.FileField(
        upload_to=user_audio_upload_path,
        max_length=255,
        null=True,
        blank=True,
        help_text="Recorded or uploaded spoken audio file.",
    )
    original_transcript = models.TextField(
        blank=True,
        default="",
        help_text="Verbatim speech recognition output.",
    )
    corrected_sentence = models.TextField(
        blank=True,
        default="",
        help_text="Grammatically corrected sentence from LLM.",
    )
    feedback = models.TextField(
        blank=True,
        default="",
        help_text="Pedagogical explanation of mistakes and corrections.",
    )

    # Scores: strictly Null if component is unavailable or uncalculated
    grammar_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Grammar accuracy (0-100%).",
    )
    pronunciation_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Acoustic phoneme-level pronunciation score (Null if unconfigured).",
    )
    fluency_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Speech rate and pause analysis score (Null if unconfigured).",
    )
    overall_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Weighted composite score based only on enabled metrics.",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )
    error_message = models.TextField(
        blank=True,
        default="",
        help_text="Safe, learner-facing error explanation when assessment fails.",
    )

    processing_duration = models.FloatField(
        null=True,
        blank=True,
        help_text="Pipeline execution time in seconds.",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"

    def __str__(self):
        return f"Assessment #{self.id} ({self.user.username}) - {self.status}"

    def delete(self, *args, **kwargs):
        """Clean up audio file from disk when record is deleted."""
        if self.audio_file and os.path.isfile(self.audio_file.path):
            try:
                os.remove(self.audio_file.path)
            except OSError:
                pass
        super().delete(*args, **kwargs)
