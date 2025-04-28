from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from notifications.models import Notification
from notifications.services.action_building import TemplateActionsBuilder
from projects.models import ProjectInvitation
from notifications.services.factories import NotificationFactory
from projects.notifications.loaders import json_loader


@receiver(post_save, sender=ProjectInvitation)
def send_invitation_notification(sender, instance, **kwargs):
    template = json_loader.get_template('invitation')
    factory = NotificationFactory(template, TemplateActionsBuilder(template))
    notification = factory.create(
        user=instance.user,
        related_object_id=instance.id
    )
    notification.save()


@receiver(post_delete, sender=ProjectInvitation)
def delete_invitation_notification(sender, instance, **kwargs):
    Notification.objects.filter(
        user=instance.user,
        object_id=instance.id,
    ).delete()
