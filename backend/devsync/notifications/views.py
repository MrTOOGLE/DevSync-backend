from django.db.models import Prefetch
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.views import ReadDeleteViewSet
from notifications.models import Notification, NotificationContextObject
from notifications.renderers import NotificationRenderer
from notifications.serializers import NotificationSerializer


class NotificationViewSet(ReadDeleteViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [NotificationRenderer]
    lookup_url_kwarg = "notification_pk"

    def get_queryset(self):
        return Notification.visible_objects.filter(
            user=self.request.user
        ).select_related(
            'content_type'
        ).prefetch_related(
            Prefetch(
                'context_objects',
                queryset=NotificationContextObject.objects.select_related(
                    'content_type'
                ).prefetch_related('content_object'),
                to_attr='prefetched_context_objects'
            )
        )

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
