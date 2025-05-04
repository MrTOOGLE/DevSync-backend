from typing import Optional, Protocol, runtime_checkable

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from notifications.models import Notification, NotificationContextObject
from notifications.services.action_building import NotificationActionsBuilder, TemplateActionsBuilder
from notifications.services.utils import apply_template_to_notification
from notifications.services.templates import NotificationTemplate


@runtime_checkable
class NotificationCreator(Protocol):
    """Protocol for classes that can create notifications."""

    def create(
            self,
            user: AbstractUser,
            related_object: Model
    ) -> Notification:
        """Create a notification for the given user and related object."""


class TemplateNotificationFactory:
    """Factory for creating notifications from templates."""

    def __init__(
            self,
            template: NotificationTemplate,
            actions_builder: Optional[NotificationActionsBuilder] = None
    ):
        self._template = template
        self._actions_builder = actions_builder or TemplateActionsBuilder(template)

    def create(self, user: AbstractUser, related_object: Model) -> Notification:
        """Create a notification for the given user and related object."""
        content_type = ContentType.objects.get_for_model(related_object)
        if content_type is None:
            raise ValueError(f"Could not determine content type for {related_object.__class__.__name__}")

        notification = Notification(
            user=user,
            content_type=content_type,
            object_id=related_object.id
        )
        apply_template_to_notification(
            notification,
            self._template,
            self._actions_builder,
        )

        return notification


class ContextObjectFactory:
    """Factory for creating notification context objects."""

    @classmethod
    def create_context_objects(
            cls,
            notification: Notification,
            context_data: dict[str, Model],
    ) -> list[NotificationContextObject]:
        """Create multiple context objects for a notification."""
        return [
            cls.create_context_object(notification, name, obj)
            for name, obj in context_data.items()
        ]

    @classmethod
    def create_context_object(
            cls,
            notification: Notification,
            name: str,
            obj: Model
    ) -> NotificationContextObject:
        """Create a single context object for a notification."""

        content_type = ContentType.objects.get_for_model(obj)
        if content_type is None:
            raise ValueError(f"Could not determine content type for {obj.__class__.__name__}")

        return NotificationContextObject(
            notification=notification,
            name=name,
            content_type=content_type,
            object_id=obj.id
        )
