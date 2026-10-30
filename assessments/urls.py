"""
Assessments URL Patterns.
"""
from django.urls import path
from assessments import views

urlpatterns = [
    path("record/", views.record_view, name="assessment_record"),
    path("<int:pk>/result/", views.result_view, name="assessment_result"),
    path("<int:pk>/detail/", views.detail_view, name="assessment_detail"),
    path("<int:pk>/delete/", views.delete_assessment_view, name="assessment_delete"),
    path("history/", views.history_view, name="assessment_history"),
    path("api/health/", views.api_system_health, name="api_system_health"),
]
