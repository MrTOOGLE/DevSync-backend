from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from notifications.models import Notification
from notifications.renderers import NotificationRenderer
from notifications.serializers import NotificationSerializer, NotificationActionSerializer
from notifications.services.actions import NotificationAction
from notifications.services.services import execute_url, update_notification_after_action, \
    display_notification_action_error
from users.permissions import IsAdminOnly


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [NotificationRenderer]
    lookup_url_kwarg = "notification_pk"

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        return {
            'request': self.request,
        }

    @action(methods=['POST'], detail=False)
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
    def clear(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return Response(
            {'success': True},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(methods=['get'], detail=False, permission_classes=[IsAdminOnly])
    def all(self, request, *args, **kwargs):
        return Response(
            {'notifications': NotificationSerializer(Notification.objects.all(), many=True).data},
            status=status.HTTP_200_OK
        )

    @action(
        methods=['post'],
        detail=True,
        url_path="actions/(?P<action_number>[0-9]+)"
    )
    def actions(self, request: Request, notification_pk=None, action_number=None):
        notification = self.get_object()
        serializer = NotificationActionSerializer(
            data={'action_number': action_number},
            context={
                'notification': notification,
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        notification_action = NotificationAction(**serializer.validated_data['action'])
        response = execute_url(
            notification_action.payload['url'],
            headers=request.headers
        )
        response_data = response.json()
        if response.status_code < 400:
            update_notification_after_action(notification_action, notification)
        elif "detail" in response_data:
            display_notification_action_error(notification, response_data['detail'])
        return Response(response_data, status=response.status_code)
