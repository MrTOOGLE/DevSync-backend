from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path("", views.index),
    path("test-mail", views.send_test_mail),
    path("v1/drf-auth/", include("rest_framework.urls")),
    re_path(r"^auth/", include("djoser.urls.authtoken")),
    path("v1/", include("djoser.urls")),
    path("v1/users/", include("users.urls")),
]