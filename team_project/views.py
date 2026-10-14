from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (SeniorProfileForm, SeniorSignupForm, StudentProfileForm,
                    StudentSignupForm)
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


def _mypage_url_name(user):
    """ユーザーの役割に応じたマイページのURL名（役割がなければ None）"""
    if StudentProfile.objects.filter(user=user).exists():
        return "student_mypage"
    if SeniorProfile.objects.filter(user=user).exists():
        return "senior_mypage"
    return None


def select_role(request):
    """新規登録: 学生か高齢者かを選ぶ"""
    if request.user.is_authenticated and _mypage_url_name(request.user):
        return redirect("mypage")
    return render(request, "select_role.html")


def _signup(request, profile_form_class, template_name):
    """アカウントとプロフィールを同時に作る（学生・高齢者で共通の処理）"""
    if request.user.is_authenticated and _mypage_url_name(request.user):
        return redirect("mypage")

    if request.method == "POST":
        user_form = UserCreationForm(request.POST)
        profile_form = profile_form_class(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user = user_form.save()
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            login(request, user)
            return redirect("mypage")
    else:
        user_form = UserCreationForm()
        profile_form = profile_form_class()

    return render(request, template_name, {
        "user_form": user_form,
        "profile_form": profile_form,
    })


def student_signup(request):
    return _signup(request, StudentSignupForm, "student_signup.html")


def senior_signup(request):
    return _signup(request, SeniorSignupForm, "senior_signup.html")


@login_required
def mypage(request):
    """役割に応じたマイページへ振り分ける（役割がなければ新規登録へ）"""
    return redirect(_mypage_url_name(request.user) or "select_role")


def _mypage(request, model, form_class, template_name, url_name):
    """プロフィールの表示と保存（学生・高齢者で共通の処理）"""
    profile = model.objects.filter(user=request.user).first()
    if profile is None:
        # 役割が違うページを開いたときは、自分のマイページへ戻す
        return redirect("mypage")

    if request.method == "POST":
        form = form_class(request.POST, instance=profile)
        if form.is_valid():
            form.save()
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


def index(request):
    return render(request, 'index.html')


# 高齢者ホーム画面を表示する関数
def elderly_home(request):
    return render(request, 'elderly_home.html')


# 待機・マッチング完了画面を表示する関数
def elderly_status(request):
    return render(request, 'elderly_status.html')