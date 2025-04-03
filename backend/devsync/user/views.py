from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from user.serializers import EmailVerificationCodeSerializer
from user.services import generate_verification_code
from user.tasks import send_verification_code_email
from user.throttling import VerificationCodeSendThrottle


class SendVerificationCodeView(APIView):
    permission_classes = (IsAuthenticated,)
    throttle_classes = (VerificationCodeSendThrottle, )

    def post(self, request: Request):
        user = request.user
        if user.is_email_verified:
            return Response(
                {"detail": "You already have an email verification."},
                status=status.HTTP_400_BAD_REQUEST
            )
        code_cache_name = settings.VERIFICATION_CODE_CACHE_NAME.format(user_id=user.pk)
        code = cache.get(code_cache_name)

        if not code:
            code = generate_verification_code()
            cache.set(code_cache_name, code, settings.EMAIL_VERIFICATION_CODE_LIFETIME)

        send_verification_code_email.delay(
            user.first_name,
            user.last_name,
            code,
            user.email,
        )
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)


class ConfirmEmailView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request: Request):
        user = request.user
        if user.is_email_verified:
            return Response(
                {"detail": "You already have an email verification."},
                status=status.HTTP_400_BAD_REQUEST
            )
        code_cache_name = settings.VERIFICATION_CODE_CACHE_NAME.format(user_id=user.pk)
        code = cache.get(code_cache_name)
        if not code:
            return Response(
                {"detail": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST
            )

        received_code = request.data.get("code", None)

        serializer = EmailVerificationCodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if code != received_code:
            return Response(
                {"detail": "Invalid verification code."},
                status=status.HTTP_400_BAD_REQUEST
            )
        cache.delete(code_cache_name)
        user.verify_email()
        return Response({"status": "success"}, status=status.HTTP_200_OK)
