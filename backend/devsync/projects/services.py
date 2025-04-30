from notifications.models import Notification
from notifications.services.action_building import TemplateActionsBuilder
from notifications.services.factories import NotificationFactory
from notifications.services.schemes import ActionName
from notifications.services.services import update_notification_by_action
from projects.models import ProjectInvitation
from projects.notifications.loaders import json_loader


class ProjectInvitationService:
    @staticmethod
    def send_invitation_notification(invitation: ProjectInvitation) -> None:
        template = json_loader.get_template('invitation')
        factory = NotificationFactory(template, TemplateActionsBuilder(template))
        notification = factory.create(
            user=invitation.user,
            related_object_id=invitation.id
        )
        notification.save()

    @classmethod
    def accept_invitation(cls, invitation: ProjectInvitation) -> None:
        cls._update_invitation_notification_by_action(invitation, 'accept')
        invitation.accept()

    @classmethod
    def reject_invitation(cls, invitation: ProjectInvitation) -> None:
        cls._update_invitation_notification_by_action(invitation, 'reject')
        invitation.reject()

    @classmethod
    def delete_invitation(cls, invitation: ProjectInvitation) -> None:
        cls._update_invitation_notification_by_action(invitation, 'delete')
        invitation.delete()

    @classmethod
    def _update_invitation_notification_by_action(
            cls,
            invitation: ProjectInvitation,
            action_name: ActionName
    ) -> None:
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

    @classmethod
    def _update_notification(cls, notification: Notification) -> None:
        pass