from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from notifications.models import Notification
from notifications.renderers import NotificationRenderer
from notifications.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'delete', 'head', 'options', 'trace']
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
