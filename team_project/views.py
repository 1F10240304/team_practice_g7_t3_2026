from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (SeniorProfileForm, SeniorSignupForm, StudentProfileForm,
                    StudentSignupForm)
from .models import HelpRequest, SeniorProfile, StudentProfile


def _open_requests(area):
    """募集中の依頼（地域が指定されていれば絞り込む）"""
    help_requests = HelpRequest.objects.filter(
        status=HelpRequest.Status.OPEN
    ).order_by("start_at")
    if area:
        help_requests = help_requests.filter(area__icontains=area)
    return help_requests


def request_list(request):
    """近くの依頼一覧（募集中のみ）"""
    area = request.GET.get("area", "")
    help_requests = _open_requests(area)

    return render(request, "request_list.html", {
        "help_requests": help_requests,
        "area": area,
    })


@require_POST
@login_required
def accept_request(request, pk):
    """依頼を引き受ける（POSTのみ・ログインした学生だけ）"""
    if _role(request.user) != "student":
        # 学生以外は引き受けられないので、自分のホームへ戻す
        return redirect("home")

    get_object_or_404(HelpRequest, pk=pk)
    # 募集中のときだけ更新する。2人が同時に押しても、引き受けられるのは1人だけ
    accepted = HelpRequest.objects.filter(
        pk=pk, status=HelpRequest.Status.OPEN
    ).update(status=HelpRequest.Status.ACCEPTED, helper=request.user)
    if not accepted:
        messages.info(request, "この依頼はすでに引き受けられています。")
    return redirect("student_home")


def _role(user):
    """ユーザーの役割（"student" / "senior"、なければ None）"""
    if StudentProfile.objects.filter(user=user).exists():
        return "student"
    if SeniorProfile.objects.filter(user=user).exists():
        return "senior"
    return None


def _mypage_url_name(user):
    """ユーザーの役割に応じたマイページのURL名（役割がなければ None）"""
    return {"student": "student_mypage", "senior": "senior_mypage"}.get(_role(user))


def _home_url_name(user):
    """ユーザーの役割に応じたホームのURL名（役割がなければ None）"""
    return {"student": "student_home", "senior": "elderly_home"}.get(_role(user))


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
            return redirect("home")
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
def home(request):
    """役割に応じたホームへ振り分ける（役割がなければ新規登録へ）"""
    return redirect(_home_url_name(request.user) or "select_role")


@login_required
def student_home(request):
    """学生ホーム: 募集中の依頼を探して引き受ける"""
    profile = StudentProfile.objects.filter(user=request.user).first()
    if profile is None:
        # 役割が違うページを開いたときは、自分のホームへ戻す
        return redirect("home")

    area = request.GET.get("area", "")
    return render(request, "student_home.html", {
        "profile": profile,
        "help_requests": _open_requests(area),
        "area": area,
    })


@login_required
def student_accepted_requests(request):
    """学生が引き受けた依頼の一覧（引き受け済みと完了に分けて表示）"""
    profile = StudentProfile.objects.filter(user=request.user).first()
    if profile is None:
        # 役割が違うページを開いたときは、自分のホームへ戻す
        return redirect("home")

    my_requests = HelpRequest.objects.filter(helper=request.user).order_by("start_at")
    return render(request, "student_accepted_requests.html", {
        "profile": profile,
        "accepted_requests": my_requests.filter(status=HelpRequest.Status.ACCEPTED),
        "done_requests": my_requests.filter(status=HelpRequest.Status.DONE),
    })


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


# ありがとう送信（レビュー）画面を表示する関数
def elderly_review(request):
    return render(request, 'elderly_review.html')


# 依頼作成（マイク）画面を表示する関数
def create_request(request):
    return render(request, 'create_request.html')
