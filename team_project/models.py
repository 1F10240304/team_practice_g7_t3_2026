from django.conf import settings
from django.db import models


class StudentProfile(models.Model):
    """学生のプロフィール"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField("名前", max_length=50)
    university = models.CharField("大学・学年", max_length=100)
    introduction = models.TextField("自己紹介", blank=True)
    skills = models.TextField("できること", blank=True)

    def __str__(self):
        return self.name


class SeniorProfile(models.Model):
    """高齢者のプロフィール"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField("名前", max_length=50)
    area = models.CharField("住んでいる地域", max_length=100)
    introduction = models.TextField("自己紹介", blank=True)
    needs = models.TextField("頼みたいこと", blank=True)

    def __str__(self):
        return self.name
