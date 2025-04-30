from dataclasses import asdict
from typing import Optional

from notifications.models import Notification
from notifications.services.action_building import NotificationActionsBuilder, TemplateActionsBuilder
from notifications.services.templates import NotificationTemplate


def apply_template_to_notification(
        notification: Notification,
        template: NotificationTemplate,
        actions_builder: Optional[NotificationActionsBuilder] = None
) -> Notification:
    for field_name in template.UPDATE_FIELDS:
        if hasattr(notification, field_name):
            setattr(notification, field_name, getattr(template, field_name))

    if actions_builder is None:
        actions_builder = TemplateActionsBuilder(template)
    actions = actions_builder.build(notification)
    notification.actions_data = {
        action_name: asdict(action) for action_name, action in actions.items()
    }

    return notification

def update_notification_footer(notification, *, footnote: str, clear_actions=False):
    notification.footnote = footnote
    if clear_actions:
        notification.actions_data = {}
    notification.save()
