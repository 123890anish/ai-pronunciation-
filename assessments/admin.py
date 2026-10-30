"""
Django Admin Registration for Assessments.
"""
from django.contrib import admin
from assessments.models import Assessment


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "grammar_score",
        "overall_score",
        "created_at",
        "processing_duration",
    )
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "original_transcript", "corrected_sentence")
    readonly_fields = ("created_at", "updated_at", "processing_duration")
