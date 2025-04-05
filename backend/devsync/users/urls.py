from django.urls import path, include
from . import views

urlpatterns = [
    path("send-code/", views.SendVerificationCodeAPIView.as_view(), name="send_verification_code"),
    path("confirm-email/", views.ConfirmEmailAPIView.as_view(), name="confirm_email"),
]
