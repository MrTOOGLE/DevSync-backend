from typing import Any, Protocol, runtime_checkable

from django.urls import reverse

from notifications.models import Notification
from notifications.services.actions import NotificationAction
from notifications.services.schemes import ActionName
from notifications.services.templates import NotificationTemplate, NotificationActionTemplate


@runtime_checkable
class NotificationActionsBuilder(Protocol):
    def build(self, notification: Notification) -> dict[ActionName, NotificationAction]:
        """Build notification actions"""


class TemplateActionsBuilder:
    def __init__(self, template: NotificationTemplate):
        self.template = template

    def build(self, notification: Notification) -> dict[ActionName, NotificationAction]:
        """Build list of NotificationAction from template"""
        actions = {}
        for action_name, action in self.template.actions.items():
            actions[action_name] = self._build_action(notification, action)
        return actions

    @classmethod
    def _build_action(cls, notification: Notification, action: NotificationActionTemplate) -> NotificationAction:
        url = cls._build_url(notification, action) if action.viewname else None
        payload = cls._build_payload(action, url)

        return NotificationAction(
            type=action.type,
            text=action.text,
            payload=payload,
            style=action.style,
        )

    @classmethod
    def _build_url(cls, notification: Notification, action: NotificationActionTemplate) -> str:
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
    def _build_payload(action: NotificationActionTemplate, url: str | None) -> dict:
        payload: dict[str, Any] = {'url': url} if url else {}
        if action.next_template:
            payload['next_template'] = action.next_template

        return payload
