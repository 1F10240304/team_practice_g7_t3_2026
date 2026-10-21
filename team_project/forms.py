from datetime import datetime

from django import forms
from django.utils import timezone

from .models import HelpRequest, SeniorProfile, StudentProfile


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


class HelpRequestForm(forms.ModelForm):
    """高齢者が確認画面で見直す依頼の内容（日にちと時間は別々に入力する）"""
    date = forms.DateField(label="日にち", widget=forms.DateInput(attrs={"type": "date"}))
    start_time = forms.TimeField(label="何時から", widget=forms.TimeInput(
        attrs={"type": "time"}, format="%H:%M"))
    end_time = forms.TimeField(label="何時まで", widget=forms.TimeInput(
        attrs={"type": "time"}, format="%H:%M"))

    class Meta:
        model = HelpRequest
        fields = ["title", "area"]
        labels = {"title": "お願いすること", "area": "場所"}

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        if start_time and end_time and end_time <= start_time:
            self.add_error("end_time", "終わりの時間は、始まりの時間より後にしてください。")
        return cleaned_data

    def save(self, commit=True):
        help_request = super().save(commit=False)
        date = self.cleaned_data["date"]
        help_request.start_at = timezone.make_aware(
            datetime.combine(date, self.cleaned_data["start_time"]))
        help_request.end_at = timezone.make_aware(
            datetime.combine(date, self.cleaned_data["end_time"]))
        if commit:
            help_request.save()
        return help_request
