import logging

from djoser.serializers import UserCreatePasswordRetypeSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdminOrOwnerOrReadOnly, IsAdminOnly
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
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminOrOwnerOrReadOnly,)

    serializer_classes = {
        'create': UserCreatePasswordRetypeSerializer
    }

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = (IsAuthenticated, IsAdminOrOwnerOrReadOnly)
        elif self.action == 'list':
            self.permission_classes = (IsAuthenticated, IsAdminOnly)

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in self.serializer_classes:
            return self.serializer_classes[self.action]
        return self.serializer_class

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

    def get_object(self):
        if self.action == 'me':
            return self.request.user
        return super().get_object()

    @action(detail=False, methods=['get', 'patch', 'delete'])
    def me(self, request, *args, **kwargs):
        if request.method == 'GET':
            return self.retrieve(request, *args, **kwargs)
        elif request.method == 'PATCH':
            return self.partial_update(request, *args, **kwargs)
        elif request.method == 'DELETE':
            return self.destroy(request, *args, **kwargs)
