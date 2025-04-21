from dataclasses import dataclass
from typing import Any, Literal

from django.test import Client


@dataclass
class NotificationAction:
    type: Literal['only_request', 'only_redirect', 'both']
    text: str
    payload: dict[str, Any]
    style: Literal['accept', 'reject', 'info', 'danger']

    def execute(self, request):
        client = Client()
        return client.post(
            self.payload['url'],
            data=request.data,
            content_type='application/json',
            HTTP_HOST='localhost',
            headers={
                'Authorization': request.headers.get('Authorization'),
                'Content-Type': 'application/json'
            }
        )
