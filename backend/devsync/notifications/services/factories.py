from typing import Optional

from django.contrib.auth import get_user_model

from notifications.models import Notification
from notifications.services.action_building import NotificationActionsBuilder, TemplateActionsBuilder
from notifications.services.utils import apply_template_to_notification
from notifications.services.templates import NotificationTemplate


User = get_user_model()


class NotificationFactory:
    def __init__(
            self,
            template: NotificationTemplate,
            actions_builder: Optional[NotificationActionsBuilder] = None
    ):
        self._template = template
        self._notification: Optional[Notification] = None
        self._action_builder = actions_builder or TemplateActionsBuilder(template)


    def create(self, user: User, related_object_id: int, content_data: Optional[dict] = None, **kwargs) -> Notification:
        notification = Notification(
            user=user,
            **kwargs
        )
        apply_template_to_notification(
            notification,
            self._template,
            related_object_id,
            content_data,
            self._action_builder,
        )

        return notification
