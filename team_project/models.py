from django.db import models

# Create your models here.

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
    created_at = models.DateTimeField(auto_now_add=True)