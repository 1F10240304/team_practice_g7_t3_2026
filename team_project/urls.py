from django.urls import path

from . import views

urlpatterns = [
    path("mypage/student/", views.student_mypage, name="student_mypage"),
    path("mypage/senior/", views.senior_mypage, name="senior_mypage"),
]
