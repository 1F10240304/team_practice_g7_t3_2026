from django.conf import settings
from django.db import models


class HelpRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "募集中"
        ACCEPTED = "accepted", "引き受け済み"
        DONE = "done", "完了"

    title = models.CharField("依頼内容", max_length=100)   # 例: 電球の交換をお願いしたいです
    area = models.CharField("地域", max_length=50)          # 例: 東京都世田谷区
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    start_at = models.DateTimeField("希望開始")
    end_at = models.DateTimeField("希望終了")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    # 依頼を引き受けた学生（募集中のあいだは空）
    helper = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="引き受けた学生",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="helped_requests",
    )
    senior = models.ForeignKey(
        "SeniorProfile", on_delete=models.CASCADE,
        related_name="help_requests", null=True, blank=True,
        verbose_name="依頼した高齢者",
    )
    created_at = models.DateTimeField(auto_now_add=True)


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


class TalkTheme(models.Model):
    """依頼が完了したときに作る、学生と高齢者の会話のきっかけ（トークテーマ）"""
    help_request = models.OneToOneField(
        HelpRequest,
        verbose_name="依頼",
        on_delete=models.CASCADE,
        related_name="talk_theme",
    )
    text = models.TextField("トークテーマ")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text
