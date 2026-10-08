from django.urls import path
from . import views

urlpatterns = [
    # 依頼
    path("requests/", views.request_list, name="request_list"),
    path("requests/<int:pk>/accept/", views.accept_request, name="accept_request"),
    # マイページ
    path("mypage/student/", views.student_mypage, name="student_mypage"),
    path("mypage/senior/", views.senior_mypage, name="senior_mypage"),
]
