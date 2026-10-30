"""
Dashboard routing module.
"""
from django.urls import path
from assessments import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
]
