import logging
from typing import Optional, Any

from notifications.models import Notification
from notifications.services.action_building import NotificationActionsBuilder
from notifications.services.actions import NotificationAction
from notifications.services.schemes import ActionName
from notifications.services.template_loading import get_template, TemplateNotFoundError
from notifications.services.templates import NotificationTemplate
from notifications.services.utils import apply_template_to_notification


logger = logging.getLogger('django')


def update_notification_by_template(
        notification: Notification,
        template: NotificationTemplate,
        related_object_id: int,
        content_data: Optional[dict[str, Any]] = None,
        actions_builder: Optional[NotificationActionsBuilder] = None
) -> Notification:
    """Applies template to notification and saves it.

    Args:
        notification: Notification instance to update
        template: Template to apply
        related_object_id: ID of related object
        content_data: Additional data for template
        actions_builder: Builder for notification actions

    Returns:
        Updated notification instance
    """
    apply_template_to_notification(
        notification,
        template,
        related_object_id,
        content_data,
        actions_builder
    )

    notification.save()
    return notification


def update_notification_by_action(
        notification: Notification,
        action_name: ActionName
) -> bool:
    """Updates notification based on specified action.

    Args:
        notification: Notification to update
        action_name: Name of action to process

    Returns:
        True if action was processed successfully, False otherwise
    """
    action = notification.actions_data.get(action_name)
    if action is None:
        return False

    try:
        action = NotificationAction(**action)
        template = get_template(action.payload['next_template'])
        content_object_id = action.payload['new_related_object_id']

        update_notification_by_template(
            notification,
            template,
            content_object_id
        )
        return True
    except (KeyError, TemplateNotFoundError) as e:
        logger.error(f"Invalid action processing: {str(e)}.")
        handle_notification_action_failure(
            notification,
            error_message=f"Не удалось выполнить действие, попробуйте позже.",
            clear_actions=False
        )
        return False


def handle_notification_action_failure(
        notification: Notification,
        *,
        error_message: str,
        clear_actions: bool = True
) -> None:
    """Handles notification action failure by updating notification state.

    Args:
        notification: Notification to update
        error_message: Error message to display
        clear_actions: Whether to clear notification actions
    """
    notification.footnote = error_message
    if clear_actions:
        notification.actions_data = {}
    notification.save()
