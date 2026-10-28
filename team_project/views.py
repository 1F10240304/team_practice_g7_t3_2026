import re
from datetime import date, time, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (HelpRequestForm, SeniorProfileForm, SeniorSignupForm,
                    StudentProfileForm, StudentSignupForm)
from . import ai
from .models import HelpRequest, SeniorProfile, StudentProfile, TalkTheme


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


# AI が使えないときのトークテーマ（依頼の内容に合わせて選ぶ）
_DEFAULT_TALK_THEMES = [
    ("電球", "昔の家の明かりや、思い出に残っている家の話を聞かせてください"),
    ("買い物", "昔よく行ったお店や、好きだった食べ物の話を聞かせてください"),
    ("掃除", "家の中で一番好きな場所や、大切にしている物の話を聞かせてください"),
    ("スマホ", "若いころの連絡の取り方や、手紙の思い出を聞かせてください"),
    ("庭", "育てたことのある花や野菜の話を聞かせてください"),
]
_FALLBACK_TALK_THEME = "最近うれしかったことや、若いころの思い出を聞かせてください"


def _talk_theme_text(help_request):
    """完了した依頼のトークテーマの文章を作る。

    AI担当が ai.py に generate_talk_theme(title) を用意したらそれを使い、
    まだないとき・失敗したときは上の決まった文章から選ぶ。
    """
    generate = getattr(ai, "generate_talk_theme", None)
    if callable(generate):
        try:
            text = generate(help_request.title)
        except Exception:
            text = ""
        if isinstance(text, str) and text.strip():
            return text.strip()

    for keyword, theme in _DEFAULT_TALK_THEMES:
        if keyword in help_request.title:
            return theme
    return _FALLBACK_TALK_THEME


@require_POST
@login_required
def complete_request(request, pk):
    """引き受けた依頼を完了にして、トークテーマを作る（POSTのみ・引き受けた学生本人だけ）"""
    # 自分が引き受けていて、引き受け済みの依頼だけを完了にできる
    help_request = get_object_or_404(
        HelpRequest, pk=pk, helper=request.user, status=HelpRequest.Status.ACCEPTED
    )
    with transaction.atomic():
        help_request.status = HelpRequest.Status.DONE
        help_request.save()
        TalkTheme.objects.get_or_create(
            help_request=help_request,
            defaults={"text": _talk_theme_text(help_request)},
        )
    return redirect("student_accepted_requests")


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

    my_requests = HelpRequest.objects.filter(helper=request.user).select_related(
        "talk_theme").order_by("start_at")
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


# ありがとう送信（レビュー）画面を表示する関数
def elderly_review(request):
    return render(request, 'elderly_review.html')


# 「明日」「6/1」などの言葉 → 何日後か・何月何日か
_RELATIVE_DAYS = {"今日": 0, "明日": 1, "明後日": 2, "あさって": 2}
# 「午前」などの言葉 → (何時から, 何時まで)
_TIME_RANGES = [
    ("午前", (9, 12)), ("午後", (13, 17)), ("朝", (9, 11)),
    ("昼", (12, 14)), ("夕方", (16, 18)), ("夜", (18, 20)),
]


def _schedule_from_text(desired_time, today):
    """AIがまとめた希望日時（例: 6/1（日）午前中）から、確認画面の日にちと時間の初期値を作る。

    読み取れないところは「明日の10時〜12時」にする。高齢者が確認画面で直せる。
    """
    day = today + timedelta(days=1)
    for word, days in _RELATIVE_DAYS.items():
        if word in desired_time:
            day = today + timedelta(days=days)
            break
    m = re.search(r"(\d{1,2})(?:/|月)(\d{1,2})", desired_time)
    if m:
        try:
            day = date(today.year, int(m.group(1)), int(m.group(2)))
            if day < today:
                day = day.replace(year=today.year + 1)
        except ValueError:
            pass

    start, end = 10, 12
    for word, hours in _TIME_RANGES:
        if word in desired_time:
            start, end = hours
            break
    m = re.search(r"(\d{1,2})時", desired_time)
    if m and int(m.group(1)) <= 21:
        start = int(m.group(1))
        end = start + 2
    return day, time(start), time(end)


def _senior_only(request):
    """高齢者でなければ自分のホームへ戻すレスポンスを返す（高齢者なら None）"""
    if _role(request.user) != "senior":
        return redirect("home")
    return None


@login_required
def create_request(request):
    """依頼作成: マイクで困りごとを話す"""
    return _senior_only(request) or render(request, "elderly_request_create.html")


@require_POST
@login_required
def confirm_request(request):
    """依頼の確認: 話した内容をAIでまとめて、高齢者に見てもらう"""
    if response := _senior_only(request):
        return response

    text = request.POST.get("text", "").strip()
    if not text:
        return render(request, "elderly_request_create.html", {
            "error": "お願いしたいことを話すか、書いてください。",
        })

    data = ai.structure_request(text)
    day, start_time, end_time = _schedule_from_text(
        data["desired_time"], timezone.localdate())
    profile = SeniorProfile.objects.get(user=request.user)
    form = HelpRequestForm(initial={
        "title": data["title"],
        "area": data["location"] or profile.area,
        "date": day,
        "start_time": start_time,
        "end_time": end_time,
    })
    return render(request, "elderly_request_confirm.html", {
        "form": form,
        "text": text,
        "desired_time": data["desired_time"],
    })


@require_POST
@login_required
def save_request(request):
    """確認画面で「これでお願いする」を押したら依頼を保存して、待機画面へ"""
    if response := _senior_only(request):
        return response

    form = HelpRequestForm(request.POST)
    if not form.is_valid():
        return render(request, "elderly_request_confirm.html", {
            "form": form,
            "text": request.POST.get("text", ""),
            "desired_time": request.POST.get("desired_time", ""),
        })

    help_request = form.save(commit=False)
    help_request.requester = request.user
    help_request.save()
    return redirect("elderly_status")


@login_required
def elderly_status(request):
    """待機・マッチング: 自分が出した依頼（完了していないもの）の今の様子"""
    if response := _senior_only(request):
        return response

    help_request = HelpRequest.objects.filter(requester=request.user).exclude(
        status=HelpRequest.Status.DONE).order_by("-created_at").first()
    if help_request is None:
        # 待っている依頼がなければホームへ
        return redirect("elderly_home")

    helper_profile = None
    if help_request.helper:
        helper_profile = StudentProfile.objects.filter(user=help_request.helper).first()
    return render(request, "elderly_status.html", {
        "help_request": help_request,
        "helper_profile": helper_profile,
    })

@login_required
def my_requests(request):
    """自分の依頼一覧: 自分が出した依頼を、新しい順にすべて表示する"""
    if response := _senior_only(request):
        return response

    my_help_requests = HelpRequest.objects.filter(
        requester=request.user
    ).select_related("helper", "talk_theme").order_by("-created_at")

    return render(request, "elderly_my_requests.html", {
        "help_requests": my_help_requests,
    })

# 学生側の依頼詳細ページを表示する関数
def student_request_detail(request, pk):
    return render(request, 'student_request_detail.html')


# 学生側の活動中（トークテーマ表示）ページ
def student_session_active(request, pk):
    return render(request, 'student_session_active.html')


# 学生側の完了報告（学びの記録）ページ
def student_review(request):
    return render(request, 'student_review.html')


# ガクチカ活動証明書ページ
def student_gakuchika(request):
    return render(request, 'student_gakuchika.html')
