from django.contrib import admin

from .models import HelpRequest, SeniorProfile, StudentProfile

admin.site.register(HelpRequest)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "university", "user"]


@admin.register(SeniorProfile)
class SeniorProfileAdmin(admin.ModelAdmin):
    list_display = ["name", "area", "user"]
