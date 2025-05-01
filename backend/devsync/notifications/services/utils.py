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
    """
    Applies a template to a notification, updating fields and actions.

    Args:
        notification: Notification instance to update
        template: Template containing the new values
        actions_builder: Builder for notification actions (defaults to TemplateActionsBuilder)
        **kwargs: Additional context for action building

    Returns:
        Updated notification instance
    """

    for field_name in template.UPDATE_FIELDS:
        if hasattr(template, field_name) and hasattr(notification, field_name):
            setattr(notification, field_name, getattr(template, field_name))

    builder = actions_builder or TemplateActionsBuilder(template)
    actions = builder.build(notification)
    notification.actions_data = {
        action_name: asdict(action) for action_name, action in actions.items()
    }

    return notification

def update_notification_footer(notification, *, footnote: str, clear_actions=False) -> Notification:
    """
    Updates notification footer text and optionally clears actions.

    Args:
        notification: Notification instance to update
        footnote: New footer text
        clear_actions: Whether to clear all actions

    Returns:
        Updated notification instance
    """

    notification.footnote = footnote
    updated_fields = ['footnote']
    if clear_actions:
        notification.actions_data = {}
        updated_fields.append('actions_data')
    notification.save(update_fields=updated_fields)
    return notification
