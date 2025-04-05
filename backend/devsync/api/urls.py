from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index),
    path("test-mail", views.send_test_mail),
    path("v1/drf-auth/", include("rest_framework.urls")),
    path("v0/", include("djoser.urls")),
    path(r"v0/auth/", include("djoser.urls.authtoken")),
    path("v1/users/", include("users.urls")),
]