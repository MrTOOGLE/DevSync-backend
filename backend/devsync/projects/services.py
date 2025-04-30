from notifications.models import Notification
from notifications.services.action_building import TemplateActionsBuilder
from notifications.services.factories import NotificationFactory
from notifications.services.schemes import ActionName
from notifications.services.services import update_notification_by_action
from projects.models import ProjectInvitation
from projects.notifications.loaders import json_loader


def send_invitation_notification(invitation: ProjectInvitation):
    template = json_loader.get_template('invitation')
    factory = NotificationFactory(template, TemplateActionsBuilder(template))
    notification = factory.create(
        user=invitation.user,
        related_object_id=invitation.id
    )
    notification.save()


def accept_invitation(invitation: ProjectInvitation):
    _update_invitation_notification(invitation, 'accept')
    invitation.accept()


def reject_invitation(invitation: ProjectInvitation):
    _update_invitation_notification(invitation, 'reject')
    invitation.reject()


def _update_invitation_notification(invitation: ProjectInvitation, action_name: ActionName):
    notification = Notification.objects.filter(
        user=invitation.user,
        object_id=invitation.id,
    ).first()
    if not notification:
        return

    update_notification_by_action(
        notification,
        action_name
    )
