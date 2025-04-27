from typing import Any, Protocol, runtime_checkable

from django.urls import reverse

from notifications.models import Notification
from notifications.services.actions import NotificationAction
from notifications.services.templates import NotificationTemplate, NotificationTemplateAction


@runtime_checkable
class NotificationActionsBuilder(Protocol):
    def build(self, notification: Notification) -> list[NotificationAction]:
        """Build notification actions"""


class TemplateActionsBuilder:
    def __init__(self, template: NotificationTemplate):
        self.template = template

    def build(self, notification: Notification) -> list[NotificationAction]:
        """Build list of NotificationAction from template"""
        return [self._build_action(notification, action) for action in self.template.actions]

    @classmethod
    def _build_action(cls, notification: Notification, action: NotificationTemplateAction) -> NotificationAction:
        url = cls._build_url(notification, action) if action.viewname else None
        payload = cls._build_payload(notification, action, url)

        return NotificationAction(
            type=action.type,
            text=action.text,
            payload=payload,
            style=action.style,
        )

    @classmethod
    def _build_url(cls, notification: Notification, action: NotificationTemplateAction) -> str:
        kwargs = {
            key: cls._format_value(notification, value)
            for key, value in action.viewname_kwargs.items()
        }
        return reverse(action.viewname, kwargs=kwargs)

    @staticmethod
    def _format_value(notification: Notification, value: str) -> Any:
        formatted = value.format(object=notification.content_object)
        return int(formatted) if formatted.isdigit() else formatted

    @staticmethod
    def _build_payload(notification: Notification, action: NotificationTemplateAction, url: str | None) -> dict:
        payload: dict[str, Any] = {'url': url} if url else {}
        if action.next_template:
            payload['next_template'] = action.next_template
        if action.new_related_object_id:
            payload['new_related_object_id'] = int(
                action.new_related_object_id.format(
                    object=notification.content_object
                )
            )
        return payload
