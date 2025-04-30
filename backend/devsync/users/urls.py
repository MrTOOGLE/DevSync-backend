from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path("users/send-code/", views.SendVerificationCodeAPIView.as_view(), name="send_verification_code"),
    path("users/confirm-email/", views.ConfirmEmailAPIView.as_view(), name="confirm_email"),
    path('', include(router.urls)),
]
