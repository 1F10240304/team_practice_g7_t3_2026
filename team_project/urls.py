from django.urls import path
from . import views

urlpatterns = [
    # 依頼
    path("requests/", views.request_list, name="request_list"),
    path("requests/<int:pk>/accept/", views.accept_request, name="accept_request"),
    path("requests/<int:pk>/complete/", views.complete_request, name="complete_request"),
    # 新規登録
    path("signup/", views.select_role, name="select_role"),
    path("signup/student/", views.student_signup, name="student_signup"),
    path("signup/senior/", views.senior_signup, name="senior_signup"),
    # ホーム
    path("home/", views.home, name="home"),
    path("home/student/", views.student_home, name="student_home"),
    path("home/student/accepted/", views.student_accepted_requests,
         name="student_accepted_requests"),
    # マイページ
    path("mypage/", views.mypage, name="mypage"),
    path("mypage/student/", views.student_mypage, name="student_mypage"),
    path("mypage/senior/", views.senior_mypage, name="senior_mypage"),
    path('', views.index, name='index'),
    path('elderly-home/', views.elderly_home, name='elderly_home'),
    path('create-request/', views.create_request, name='create_request'),
    path('elderly-status/', views.elderly_status, name='elderly_status'),
    path('elderly-review/', views.elderly_review, name='elderly_review'),   # ← 追加
    path('requests/new/', views.create_request, name='create_request'),     # ← 追加
    path('elderly-review/', views.elderly_review, name='elderly_review'),
]
