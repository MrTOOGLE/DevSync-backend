from typing import Optional, Any, Protocol, runtime_checkable

from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from notifications.models import Notification, NotificationContextObject
from notifications.services.action_building import NotificationActionsBuilder, TemplateActionsBuilder
from notifications.services.utils import apply_template_to_notification
from notifications.services.templates import NotificationTemplate


@runtime_checkable
class NotificationCreator(Protocol):
    def create(
            self,
            user: AbstractUser,
            related_object: Model
    ) -> Notification:
        pass


class TemplateNotificationFactory:
    def __init__(
            self,
            template: NotificationTemplate,
            actions_builder: Optional[NotificationActionsBuilder] = None
    ):
        self._template = template
        self._action_builder = actions_builder or TemplateActionsBuilder(template)

    def create(self, user: AbstractUser, related_object: Model) -> Notification:
        notification = Notification(
            user=user,
            content_type=ContentType.objects.get_for_model(related_object),
            object_id=related_object.id
        )
        apply_template_to_notification(
            notification,
            self._template,
            self._action_builder,
        )

        return notification


class ContextObjectFactory:
    @classmethod
    def create_context_objects(
            cls,
            notification: Notification,
            context_data: dict[str, Model],
    ) -> list[NotificationContextObject]:
        context_objects = []
        for name, obj in context_data.items():
            context_objects.append(
                cls.create_context_object(notification, name, obj)
            )
        return context_objects

    @classmethod
    def create_context_object(
            cls,
            notification: Notification,
            name: str,
            obj: Any
    ) -> NotificationContextObject:
        return NotificationContextObject(
            notification=notification,
            name=name,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id
        )
