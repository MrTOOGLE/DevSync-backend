from typing import Optional, Type

from rest_framework.request import Request
from rest_framework.response import Response

from config.utils.executors import RequestExecutorWithTokenAuth, RequestExecutor
from notifications.models import Notification
from notifications.services.action_building import NotificationActionsBuilder
from notifications.services.actions import NotificationAction
from notifications.services.template_loading import get_template
from notifications.services.templates import NotificationTemplate
from notifications.services.utils import apply_template_to_notification


def update_notification_with_template_actions(
        notification: Notification,
        template: NotificationTemplate,
        related_object_id: int,
        content_data: Optional[dict] = None,
        actions_builder: Optional[NotificationActionsBuilder] = None,
        **kwargs
) -> Notification:
    apply_template_to_notification(
        notification,
        template,
        related_object_id,
        content_data,
        actions_builder
    )

    for key, value in kwargs.items():
        setattr(notification, key, value)

    notification.save()
    return notification


def execute_url(
        url: str,
        *,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        request_executor: Type[RequestExecutor] = RequestExecutorWithTokenAuth,
) -> Response:

    response = request_executor().execute(
        url,
        headers=headers or {'Content-Type': 'application/json'},
        data=data or {},
        method="POST"
    )

    return response


def update_notification_after_action(
    notification: Notification,
    action: NotificationAction
) -> None:
    template_name = action.payload['next_template']
    template = get_template(template_name)
    content_object_id = action.payload['new_related_object_id']
    update_notification_with_template_actions(
        notification,
        template,
        content_object_id
    )


def display_notification_action_error(notification: Notification) -> None:
    notification.footnote = 'Не удалось обработать данное действие.'
    notification.actions_data = []
    notification.save()


def execute_action(notification: Notification, action_data: dict[str, any], request: Request) -> Response:
    notification_action = NotificationAction(**action_data)
    response = execute_url(
        notification_action.payload['url'],
        headers=request.headers
    )

    if response.status_code < 400:
        update_notification_after_action(notification, notification_action)
    else:
        display_notification_action_error(notification)
    return response
