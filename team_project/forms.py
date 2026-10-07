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
