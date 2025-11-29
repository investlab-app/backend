import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

http_application = get_asgi_application()

from config.urls import websocket_urlpatterns  # noqa: E402
from modules.authentication.middlewares import (  # noqa: E402
    CookieWebsocketAuthMiddleware,
)

application = ProtocolTypeRouter(
    {
        "http": http_application,
        "websocket": AllowedHostsOriginValidator(
            CookieWebsocketAuthMiddleware(
                AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
            )
        ),
    },
)
