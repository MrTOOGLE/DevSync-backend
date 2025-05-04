import logging
from abc import abstractmethod, ABC
from typing import Optional, TypeVar, Generic, Any

from django.contrib.auth.models import AbstractUser
from django.db import models

from notifications.models import Notification, NotificationContextObject
from notifications.services.action_building import TemplateActionsBuilder
from notifications.services.actions import NotificationAction
from notifications.services.factories import ContextObjectFactory, NotificationCreator
from notifications.services.schemes import ActionName
from notifications.services.template_loading import NotificationTemplateNotFoundError, NotificationTemplateLoader
from notifications.services.utils import apply_template_to_notification, update_notification_footer

logger = logging.getLogger('django')

T = TypeVar('T', bound=models.Model)


class NotificationServiceBase(ABC, Generic[T]):
    """Abstract base class for notification services."""

    @abstractmethod
    def create_notification(self, user: AbstractUser, related_object: T, **kwargs: Any) -> Notification:
        """Create a new notification."""

    @abstractmethod
    def get_notification(self, user: AbstractUser, related_object: T, **kwargs: Any) -> Optional[Notification]:
        """Retrieve an existing notification."""

    @abstractmethod
    def update_notification_by_action(
            self,
            user: AbstractUser,
            related_object: T,
            action_name: ActionName,
    ) -> Optional[Notification]:
        """Update notification based on user action."""

    @abstractmethod
    def delete_notification(self, user: AbstractUser, related_object: T, **kwargs: Any) -> None:
        """Delete a notification."""


class NotificationService(NotificationServiceBase[T]):
    def __init__(
            self,
            template_loader: NotificationTemplateLoader,
            factory: NotificationCreator,
    ):
        self._template_loader = template_loader
        self._factory = factory

    def create_notification(self, user: AbstractUser, related_object: T, **kwargs) -> Notification:
        notification = self._factory.create(
            user,
            related_object
        )
        notification.save()
        return notification

    def get_notification(self, user: AbstractUser, related_object: T, **kwargs) -> Optional[Notification]:
        try:
            return Notification.objects.filter(
                user=user,
                object_id=related_object.id,
            ).latest()
        except Notification.DoesNotExist:
            logger.warning(f"No notification found for {user} by {related_object}.", exc_info=True)
            return None

    def update_notification_by_action(
            self,
            user: AbstractUser,
            related_object: T,
            action_name: ActionName,
    ) -> Optional[Notification]:
        notification = self.get_notification(user, related_object)
        if not notification:
            return None

        action = notification.actions_data.get(action_name)
        if action is None:
            return notification

        try:
            action = NotificationAction(**action)
            template = self._template_loader.get_template(action.payload['next_template'])
            apply_template_to_notification(
                notification,
                template,
                TemplateActionsBuilder(template)
            )
            notification.save()
        except (KeyError, NotificationTemplateNotFoundError) as e:
            logger.error(f"Invalid action processing: {str(e)}.")
            update_notification_footer(
                notification,
                footnote=f"Что-то пошло не так... Скажите бэку...",
                clear_actions=False
            )
            return notification

    def delete_notification(self, user: AbstractUser, related_object: T, **kwargs):
        notification = self.get_notification(user, related_object)
        if not notification:
            return
        notification.delete()


class NotificationContextServiceBase(ABC):
    """Abstract base class for notification context services."""

    @staticmethod
    @abstractmethod
    def create_context(
            notification: Notification,
            context_data: dict[str, models.Model]
    ) -> list[NotificationContextObject]:
        """Create notification context objects."""


class NotificationContextService(NotificationContextServiceBase):
    @staticmethod
    def create_context(
            notification: Notification,
            context_data: dict[str, models.Model]
    ) -> list[NotificationContextObject]:
        if not context_data:
            return []

        context_objects = ContextObjectFactory.create_context_objects(
            notification,
            context_data
        )
        return NotificationContextObject.objects.bulk_create(context_objects)
