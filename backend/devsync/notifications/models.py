from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

User = get_user_model()


class VisibleNotificationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_hidden=False)


class NotificationContextObject(models.Model):
    notification = models.ForeignKey('Notification', on_delete=models.CASCADE, related_name='context_objects')
    name = models.CharField(max_length=64, blank=False, null=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['notification', 'name'], name='unique_notification'),
        ]


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    message = models.CharField(max_length=256)
    is_read = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    actions_data = models.JSONField(default=dict)
    footnote = models.CharField(max_length=256, null=True, blank=True)

    objects = models.Manager()
    visible_objects = VisibleNotificationManager()

    class Meta:
        ordering = ['-created_at']
        get_latest_by = 'created_at'
        indexes = [
            models.Index(
                name='user_visible_notifications_idx',
                fields=['user'],
                condition=models.Q(is_hidden=False)
            ),
            models.Index(
                fields=['created_at']
            )
        ]

    @property
    def formatted_message(self):
        try:
            context_data = {
                context.name: context.content_object
                for context in self.context_objects.all()
            }
            return self.message.format(**context_data)
        except (KeyError, AttributeError):
            return self.message

    def read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])

    def hide(self):
        self.is_hidden = True
        self.save(update_fields=['is_hidden'])

    def __str__(self):
        return f"Notification <{self.title}> for {self.user}"


@receiver(post_save, sender=Notification)
def notification_updated(sender, instance, created, **kwargs):
    update_fields = kwargs['update_fields']
    is_only_read_updated = update_fields == frozenset(['is_read'])

    if instance.is_hidden or is_only_read_updated:
        return

    from .serializers import NotificationSerializer

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f'user_{instance.user.id}',
        {
            'type': 'send_notification',
            'notification': {
                'id': instance.id,
                'type': 'UPDATE' if not created else 'NEW',
                'data': NotificationSerializer(instance).data
            }
        }
    )


@receiver(post_delete, sender=Notification)
def notification_deleted(sender, instance, **kwargs):
    if instance.is_hidden:
        return

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f'user_{instance.user.id}',
        {
            'type': 'send_notification',
            'notification': {
                'id': instance.id,
                'type': 'DELETE',
                'data': {}
            }
        }
    )
