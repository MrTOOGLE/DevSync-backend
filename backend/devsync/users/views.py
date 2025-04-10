import logging

from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdminOrOwnerOrReadOnly
from .serializers import ConfirmEmailSerializer, SendVerificationCodeSerializer, UserSerializer
from .throttling import VerificationCodeSendThrottle
from .models import User

logger = logging.getLogger('__name__')


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


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminOrOwnerOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
