from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import UserViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')


urlpatterns = [
    path('', include(router.urls)),
    path("send-code/", views.SendVerificationCodeAPIView.as_view(), name="send_verification_code"),
    path("confirm-email/", views.ConfirmEmailAPIView.as_view(), name="confirm_email"),
]
