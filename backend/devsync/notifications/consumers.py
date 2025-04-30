import json
import logging
from typing import Any, Optional, Awaitable, Callable, Self
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger: logging.Logger = logging.getLogger('django')


class NotificationConsumer(AsyncWebsocketConsumer):
    _HANDLERS: dict[str, Callable[[Self, dict[str, Any]], Awaitable[None]]] = {
        'mark_as_read': lambda self, data: self._handle_mark_as_read(data),
        'mark_all_read': lambda self, data: self._handle_mark_all_read(data),
        'mark_as_hidden': lambda self, data: self._handle_mark_as_hidden(data),
        'mark_all_hidden': lambda self, data: self._handle_mark_all_hidden(data),
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.user: Optional['User'] = None
        self.group_name: Optional[str] = None
        self.connection_id: Optional[str] = None

    async def connect(self) -> None:
        self.user = self.scope.get('user')

        if not self.user:
            await self.close(code=4001)
            return
        self.connection_id = id(self)
        logger.info(
            f"User {self.user.id} connected (conn_id: {self.connection_id})"
        )
        await self._setup_user_group()
        await self.accept()

    async def disconnect(self, close_code: int) -> None:
        if self.group_name:
            await self._remove_from_group()

        logger.info(
            f"User {self.user.id} disconnected (conn_id: {self.connection_id}, "
            f"code: {close_code})"
        )

    async def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None) -> None:
        try:
            if text_data:
                await self._process_message(text_data)
        except json.JSONDecodeError:
            logger.warning(
                f"Invalid JSON received from user {self.user.id} "
                f"(conn_id: {self.connection_id})"
            )
            await self._send_error("Invalid JSON format")
        except Exception as e:
            logger.error(
                f"Error processing message from user {self.user.id}: {str(e)} "
                f"(conn_id: {self.connection_id})",
                exc_info=True
            )
            await self._send_error("Internal server error")

    async def send_notification(self, event: dict[str, Any]) -> None:
        try:
            await self._send_message(
                message_type="notification",
                payload=event['notification']
            )
            logger.debug(
                f"Notification sent to user {self.user.id} "
                f"(conn_id: {self.connection_id})"
            )
        except Exception as e:
            logger.error(
                f"Failed to send notification to user {self.user.id}: {str(e)} "
                f"(conn_id: {self.connection_id})",
                exc_info=True
            )

    @database_sync_to_async
    def read_notification(self, notification_id: int) -> None:
        from .models import Notification

        if notification := Notification.objects.filter(
                id=notification_id,
                user=self.user
        ).first():
            notification.read()

    @database_sync_to_async
    def read_all_notifications(self) -> None:
        from .models import Notification

        Notification.objects.filter(
            user=self.user,
            is_read=False
        ).update(is_read=True)

    @database_sync_to_async
    def hide_notification(self, notification_id: int) -> None:
        from .models import Notification

        if notification := Notification.objects.filter(
                id=notification_id,
                user=self.user
        ).first():
            notification.hide()

    @database_sync_to_async
    def hide_all_notifications(self) -> None:
        from .models import Notification

        Notification.objects.filter(
            user=self.user,
            is_hidden=False
        ).update(is_hidden=True)

    async def _process_message(self, text_data: str) -> None:
        data: dict[str, Any] = json.loads(text_data)
        message_type: Optional[str] = data.get('type')

        if not message_type:
            await self._send_error("Message type is required")
            return

        if handler := self._HANDLERS.get(message_type):
            logger.debug(
                f"Process message <{message_type}> from user {self.user.id} "
                f"(conn_id: {self.connection_id})"
            )
            await handler(self, data)
        else:
            await self._send_error(f"Unknown message type: {message_type}")

    async def _handle_mark_as_read(self, data: dict[str, Any]) -> None:
        if not (notification_id := data.get('notification_id')):
            await self._send_error("notification_id is required")
            return

        await self.read_notification(notification_id)

    async def _handle_mark_all_read(self, data: dict[str, Any]) -> None:
        await self.read_all_notifications()

    async def _handle_mark_as_hidden(self, data: dict[str, Any]) -> None:
        if not (notification_id := data.get('notification_id')):
            await self._send_error("notification_id is required")
            return

        await self.hide_notification(notification_id)

    async def _handle_mark_all_hidden(self, data: dict[str, Any]) -> None:
        await self.hide_all_notifications()

    async def _send_message(self, message_type: str, payload: Any) -> None:
        await self.send(text_data=json.dumps({
            "type": message_type,
            "data": payload
        }))

    async def _send_error(self, error_message: str) -> None:
        await self._send_message("error", {"message": error_message})

    async def _setup_user_group(self) -> None:
        self.group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

    async def _remove_from_group(self) -> None:
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
