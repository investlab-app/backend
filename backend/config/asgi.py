"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path

from config.urls import websocket_urlpatterns  # noqa: E402
from modules.authentication.middlewares import JWTAuthMiddleware

http_application = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": URLRouter(
            [re_path("^", http_application)]  # type: ignore [arg-type]
        ),
        "websocket": JWTAuthMiddleware(
            AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        ),
    },
)
