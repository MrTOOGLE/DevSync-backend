from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import Notification
from notifications.renderers import NotificationRenderer
from notifications.serializers import NotificationSerializer, NotificationActionSerializer
from notifications.services.actions import NotificationAction
from users.permissions import IsAdminOnly


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [NotificationRenderer]
    lookup_url_kwarg = "notification_pk"

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

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
            context={'notification': notification}
        )
        serializer.is_valid(raise_exception=True)

        action_data = serializer.validated_data['action']
        payload = action_data['payload']

        response = NotificationAction(**action_data).execute(request)

        if response.status_code < 300 and 'to_template' in payload:
            serializer.update_notification()
        return Response(response.json(), status=response.status_code)
