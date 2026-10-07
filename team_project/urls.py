from django.urls import path
from . import views

urlpatterns = [
    path("", views.request_list, name="request_list"),
    path("<int:pk>/accept/", views.accept_request, name="accept_request"),
]