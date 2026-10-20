from django.contrib import admin

from .models import HelpRequest, SeniorProfile, StudentProfile


@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    # 一覧で依頼の内容と状態がひと目で分かるようにする
    list_display = ["title", "area", "start_at", "end_at", "status", "created_at"]
    # 状態（募集中・引き受け済み・完了）で絞り込めるようにする
    list_filter = ["status"]
    # 依頼内容と地域で検索できるようにする
    search_fields = ["title", "area"]
    # 新しい依頼が上に来るようにする
    ordering = ["-created_at"]


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "university", "user"]


@admin.register(SeniorProfile)
class SeniorProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "area", "user"]