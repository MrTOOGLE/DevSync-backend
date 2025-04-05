from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import ConfirmEmailSerializer, SendVerificationCodeSerializer
from .throttling import VerificationCodeSendThrottle


class SendVerificationCodeAPIView(APIView):
    throttle_classes = (VerificationCodeSendThrottle, )

    def post(self, request: Request):
        serializer = SendVerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"status": "success"}, status=status.HTTP_201_CREATED)


class ConfirmEmailAPIView(APIView):
    def post(self, request: Request):
        serializer = ConfirmEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"status": "success"}, status=status.HTTP_200_OK)
