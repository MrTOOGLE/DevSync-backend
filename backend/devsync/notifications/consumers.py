import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        self.group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'mark_as_read':
            notification_id = text_data_json.get('notification_id')
            await self.mark_notification_as_read(notification_id)

    async def send_notification(self, event):
        notification_data = event['notification']
        await self.send(text_data=json.dumps(notification_data))

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        from .models import Notification

        notification = Notification.objects.filter(
            id=notification_id,
            user=self.user
        ).first()
        if notification:
            notification.read()
