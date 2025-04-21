from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from notifications.models import Notification
from projects.models import ProjectInvitation
from notifications.services.factory import NotificationFactory


@receiver(post_save, sender=ProjectInvitation)
def send_invitation_notification(sender: ProjectInvitation, instance, **kwargs):
    factory = NotificationFactory("invitation")
    factory.create(
        user=instance.user,
        related_object_id=instance.id
    )


@receiver(post_delete, sender=ProjectInvitation)
def delete_invitation_notification(sender: ProjectInvitation, instance, **kwargs):
    Notification.objects.filter(
        user=instance.user,
        object_id=instance.id,
    )
