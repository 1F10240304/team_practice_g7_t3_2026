from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SeniorProfileForm, StudentProfileForm
from .models import HelpRequest, SeniorProfile, StudentProfile


def request_list(request):
    """近くの依頼一覧（募集中のみ）"""
    help_requests = HelpRequest.objects.filter(
        status=HelpRequest.Status.OPEN
    ).order_by("start_at")

    area = request.GET.get("area", "")
    if area:
        help_requests = help_requests.filter(area__icontains=area)

    return render(request, "request_list.html", {
        "help_requests": help_requests,
        "area": area,
    })


@require_POST
def accept_request(request, pk):
    """依頼を引き受ける（POSTのみ）"""
    help_request = get_object_or_404(
        HelpRequest, pk=pk, status=HelpRequest.Status.OPEN
    )
    help_request.status = HelpRequest.Status.ACCEPTED
    help_request.save()
    return redirect("request_list")


def _mypage(request, model, form_class, template_name, url_name):
    """プロフィールの表示と保存（学生・高齢者で共通の処理）"""
    profile = model.objects.filter(user=request.user).first()

    if request.method == "POST":
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect(url_name)
    else:
        form = form_class(instance=profile)

    return render(request, template_name, {"profile": profile, "form": form})


@login_required
def student_mypage(request):
    return _mypage(request, StudentProfile, StudentProfileForm,
                   "student_mypage.html", "student_mypage")


@login_required
def senior_mypage(request):
    return _mypage(request, SeniorProfile, SeniorProfileForm,
                   "senior_mypage.html", "senior_mypage")
