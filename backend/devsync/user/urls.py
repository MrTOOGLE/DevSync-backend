from django.urls import path
from . import views

urlpatterns = [
    path("send-code/", views.SendVerificationCodeView.as_view(), name="send_verification_code"),
    path("confirm-email/", views.ConfirmEmailView.as_view(), name="confirm_email")
]