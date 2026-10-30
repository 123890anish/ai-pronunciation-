"""
Assessments Views.
Enforces user isolation, handles recording uploads, displays scoreboards, and renders history.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from assessments.forms import AudioSubmissionForm
from assessments.models import Assessment
from assessments.services import get_dashboard_context, process_user_audio_assessment
from configure import get_config
from llm.model import check_ollama_health


@login_required
def dashboard_view(request):
    """Render personalized learning dashboard with statistics and scoreboard."""
    ctx = get_dashboard_context(request.user)
    return render(request, "dashboard/index.html", ctx)


@login_required
def record_view(request):
    """
    Audio recording and file upload page.
    Supports standard HTML multipart POST and AJAX submissions.
    """
    config = get_config()
    ollama_health = check_ollama_health()

    if request.method == "POST":
        form = AudioSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            audio_file = form.cleaned_data["audio_file"]
            result = process_user_audio_assessment(
                user=request.user,
                audio_file=audio_file,
                filename=audio_file.name,
                content_type=audio_file.content_type,
            )

            # Check if this was an AJAX request
            if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
                if result.success:
                    return JsonResponse({
                        "success": True,
                        "redirect_url": f"/assessments/{result.assessment_id}/result/",
                    })
                return JsonResponse({
                    "success": False,
                    "error": result.error_message or "Assessment failed.",
                }, status=400)

            if result.success:
                messages.success(request, "Audio processed and assessed successfully!")
                return redirect("assessment_result", pk=result.assessment_id)
            else:
                messages.error(request, result.error_message or "Assessment processing failed.")
                return redirect("assessment_result", pk=result.assessment_id)
        else:
            errors = form.errors.as_text()
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": False, "error": errors}, status=400)
            messages.error(request, f"Upload error: {errors}")
    else:
        form = AudioSubmissionForm()

    return render(request, "assessments/record.html", {
        "form": form,
        "config": config,
        "ollama_health": ollama_health,
    })


@login_required
def result_view(request, pk: int):
    """
    Display comprehensive assessment outcome with transcript, corrected sentence,
    pedagogical feedback, and transparent scoreboard.
    Strictly enforces user isolation: 404 if record belongs to someone else.
    """
    assessment = get_object_or_404(Assessment, pk=pk, user=request.user)
    config = get_config()

    pronunciation_notice = None
    if not config.assessment.pronunciation_scoring_enabled:
        pronunciation_notice = "Pronunciation score unavailable — phoneme-level assessment is not configured."

    fluency_notice = None
    if not config.assessment.fluency_scoring_enabled:
        fluency_notice = "Fluency score unavailable — acoustic pause/speech-rate model is not configured."

    return render(request, "assessments/result.html", {
        "assessment": assessment,
        "config": config,
        "pronunciation_notice": pronunciation_notice,
        "fluency_notice": fluency_notice,
    })


@login_required
def history_view(request):
    """
    Display paginated chronological assessment history for the authenticated user.
    """
    user_assessments = Assessment.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(user_assessments, 10)  # 10 items per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "assessments/history.html", {
        "page_obj": page_obj,
        "total_count": user_assessments.count(),
    })


@login_required
def detail_view(request, pk: int):
    """Detail view for a historical assessment record."""
    assessment = get_object_or_404(Assessment, pk=pk, user=request.user)
    return render(request, "assessments/detail.html", {
        "assessment": assessment,
    })


@login_required
@require_POST
def delete_assessment_view(request, pk: int):
    """
    Allow user to delete their own assessment and associated audio recording.
    Enforces user data privacy.
    """
    assessment = get_object_or_404(Assessment, pk=pk, user=request.user)
    assessment.delete()
    messages.success(request, "Assessment record and audio recording deleted.")
    return redirect("assessment_history")


@login_required
def api_system_health(request):
    """JSON API to check Ollama daemon status."""
    health = check_ollama_health()
    return JsonResponse(health)
