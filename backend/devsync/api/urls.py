from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index),
    path("v1/users/", include("users.urls")),
    path(r"v1/auth/", include("djoser.urls.authtoken")),
]
