from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path("", views.index),
    path("v1/drf-auth/", include("rest_framework.urls")),
    path("v1/auth/", include("djoser.urls")),
    re_path(r"^auth/", include("djoser.urls.authtoken")),
]