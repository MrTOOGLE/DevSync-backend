import logging
from abc import ABCMeta, abstractmethod
from typing import Optional, TypeVar, Generic

from django.contrib.auth.models import AbstractUser
from django.db import models

from notifications.models import Notification, NotificationContextObject
from notifications.services.action_building import TemplateActionsBuilder
from notifications.services.actions import NotificationAction
from notifications.services.factories import ContextObjectFactory, NotificationCreator
from notifications.services.schemes import ActionName
from notifications.services.template_loading import TemplateNotFoundError, TemplateLoader
from notifications.services.utils import apply_template_to_notification, update_notification_footer

logger = logging.getLogger('django')

T = TypeVar('T', bound=models.Model)


class NotificationServiceBase(Generic[T], metaclass=ABCMeta):
    @abstractmethod
    def create_notification(self, user: AbstractUser, related_object: T, **kwargs) -> Notification:
        pass

    @abstractmethod
    def get_notification(self, user: AbstractUser, related_object: T, **kwargs) -> Notification:
        pass

    @abstractmethod
    def update_notification_by_action(
            self,
            user: AbstractUser,
            related_object: T,
            action_name: ActionName,
    ) -> Optional[Notification]:
        pass

    @abstractmethod
    def delete_notification(self, user: AbstractUser, related_object: T, **kwargs) -> None:
        pass


class NotificationService(NotificationServiceBase, Generic[T]):
    def __init__(
            self,
            template_loader: TemplateLoader,
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
            logger.warning(f"No notification found for {user} by {related_object}.")
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
        except (KeyError, TemplateNotFoundError) as e:
            logger.error(f"Invalid action processing: {str(e)}.")
            update_notification_footer(
                notification,
                footnote=f"Что-то пошло не так... Скажите бэку...",
                clear_actions=False
            )
            return notification

    def delete_notification(self, user: AbstractUser, related_object: T, **kwargs):
        notification = self.get_notification(user, related_object)
        print(notification)
        if not notification:
            return
        notification.delete()


class NotificationContextServiceBase(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def create_context(
            notification: Notification,
            context_data: dict[str, models.Model]
    ) -> list[NotificationContextObject]:
        pass


class NotificationContextService(NotificationContextServiceBase):
    @staticmethod
    def create_context(
            notification: Notification,
            context_data: dict[str, models.Model]
    ) -> list[NotificationContextObject]:
        context_objects = ContextObjectFactory.create_context_objects(
            notification,
            context_data
        )
        return NotificationContextObject.objects.bulk_create(context_objects)
