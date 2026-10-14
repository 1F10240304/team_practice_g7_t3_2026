from django.urls import path
from . import views

urlpatterns = [
    # 依頼
    path("requests/", views.request_list, name="request_list"),
    path("requests/<int:pk>/accept/", views.accept_request, name="accept_request"),
    # 新規登録
    path("signup/", views.select_role, name="select_role"),
    path("signup/student/", views.student_signup, name="student_signup"),
    path("signup/senior/", views.senior_signup, name="senior_signup"),
    # マイページ
    path("mypage/", views.mypage, name="mypage"),
    path("mypage/student/", views.student_mypage, name="student_mypage"),
    path("mypage/senior/", views.senior_mypage, name="senior_mypage"),
    path('', views.index, name='index'),
    path('elderly-home/', views.elderly_home, name='elderly_home'),
]
