from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from notifications.models import Notification
from notifications.renderers import NotificationRenderer
from notifications.serializers import NotificationSerializer, NotificationActionSerializer
from notifications.services.services import execute_action


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [NotificationRenderer]
    lookup_url_kwarg = "notification_pk"

    def get_queryset(self):
        return Notification.visible_objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {
            'request': self.request,
        }

    @action(methods=['put'], detail=False)
    def mark_as_read(self, request, *args, **kwargs):
        Notification.objects.filter(
            user=self.request.user,
            is_read=False
        ).update(is_read=True)
        return Response(
            {'success': True},
            status=status.HTTP_200_OK
        )

    @action(methods=['delete'], detail=False)
    def all(self, request, *args, **kwargs):
        self.get_queryset().update(is_hidden=True)
        return Response(
            {'success': True},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(methods=['post'],detail=True, url_path='action')
    def do_action(self, request: Request, notification_pk=None):
        notification = self.get_object()
        serializer = NotificationActionSerializer(
            data=request.data,
            context={'notification': notification}
        )
        serializer.is_valid(raise_exception=True)
        response = execute_action(
            notification,
            serializer.validated_data['action'],
            request
        )
        return Response(
            {'success': True},
            status=response.status_code
        )
