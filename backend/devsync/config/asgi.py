import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import notifications.routing
from notifications.middleware import TokenBasedAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenBasedAuthMiddleware(
        URLRouter(
            notifications.routing.websocket_urlpatterns
        )
    ),
})
