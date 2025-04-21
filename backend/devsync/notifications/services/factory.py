from dataclasses import asdict
from typing import Optional

from notifications.models import Notification
from notifications.services.builders import NotificationTemplatesBuilder, ActionBuilder


class NotificationFactory:
    def __init__(self, template_name: str, notification: Optional[Notification] = None):
        self._template = NotificationTemplatesBuilder.get_templates().get(template_name)
        self._notification: Optional[Notification] = notification

    def create(self, user, related_object_id, **kwargs) -> Notification:
        notification = Notification.objects.create(
            user=user,
            title=self._template.title,
            message=self._template.message,
            content_type=self._template.content_type,
            object_id=related_object_id,
            content_data=kwargs
        )

        self._notification = notification
        actions = ActionBuilder(self._template, self._notification).build()
        if actions:
            notification.actions_data = {
                "actions": [asdict(action) for action in actions]
            }
            notification.save()

        return notification

    def update(self, related_object_id, **kwargs) -> Notification:
        self._notification.title = self._template.title
        self._notification.message = self._template.message
        self._notification.content_type = self._template.content_type
        self._notification.object_id = related_object_id
        self._notification.content_data = kwargs
        self._notification.actions_data = ActionBuilder(self._template, self._notification).build()
        self._notification.save()

        return self._notification

