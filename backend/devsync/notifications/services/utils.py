from dataclasses import asdict
from typing import Optional

from notifications.models import Notification
from notifications.services.action_building import NotificationActionsBuilder, TemplateActionsBuilder
from notifications.services.templates import NotificationTemplate


def apply_template_to_notification(
        notification: Notification,
        template: NotificationTemplate,
        related_object_id: int,
        content_data: Optional[dict] = None,
        actions_builder: Optional[NotificationActionsBuilder] = None
) -> Notification:
    for field_name in template.MAPPED_FIELDS:
        if hasattr(notification, field_name):
            setattr(notification, field_name, getattr(template, field_name))

    notification.object_id = related_object_id
    notification.content_data = content_data or {}

    if actions_builder is None:
        actions_builder = TemplateActionsBuilder(template)

    notification.actions_data = [
        asdict(action) for action in actions_builder.build(notification)
    ]

    return notification
