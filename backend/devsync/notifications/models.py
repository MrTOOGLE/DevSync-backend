from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

User = get_user_model()


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    message = models.CharField(max_length=256)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    content_data = models.JSONField(default=dict)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    actions_data = models.JSONField(default=dict)
    footnote = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['user']
            ),
            models.Index(
                name='auto_expire_idx',
                fields=['created_at'],
                condition=models.Q(created_at__lt=now() - timedelta(weeks=2)),
            )
        ]

    @property
    def formatted_message(self):
        try:
            return self.message.format(**self.content_data, object=self.content_object)
        except (KeyError, AttributeError) as e:
            return self.message

    def read(self):
        self.is_read = True
        self.save()

    def __str__(self):
        return f"<{self.title}> for {self.user}"


@receiver(post_save, sender=Notification)
def notification_updated(sender, instance, created, **kwargs):
    from .serializers import NotificationSerializer

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f'user_{instance.user.id}',
        {
            'type': 'send_notification',
            'notification': {
                'id': instance.id,
                'type': 'UPDATE' if not created else 'CREATE',
                'data': NotificationSerializer(instance).data
            }
        }
    )
