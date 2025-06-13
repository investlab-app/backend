"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from config.urls import sse_urlpatterns

http_application = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": URLRouter(
            sse_urlpatterns
            + [re_path("^", http_application)]  # type: ignore [arg-type]
        ),
    }
)
