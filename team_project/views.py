from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SeniorProfileForm, StudentProfileForm
from .models import SeniorProfile, StudentProfile


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
