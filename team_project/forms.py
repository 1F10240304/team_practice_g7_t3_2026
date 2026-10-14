from django import forms

from .models import SeniorProfile, StudentProfile


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ["name", "university", "introduction", "skills"]


class SeniorProfileForm(forms.ModelForm):
    class Meta:
        model = SeniorProfile
        fields = ["name", "area", "introduction", "needs"]


class StudentSignupForm(forms.ModelForm):
    """学生の新規登録で入力するプロフィール項目"""
    class Meta:
        model = StudentProfile
        fields = ["name", "university"]


class SeniorSignupForm(forms.ModelForm):
    """高齢者の新規登録で入力するプロフィール項目"""
    class Meta:
        model = SeniorProfile
        fields = ["name", "area"]
