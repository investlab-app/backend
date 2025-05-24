from django.urls import re_path

from modules.prices.consumers import TestConsumer

websocket_urlpatterns = [
    re_path(r"ws/test/$", TestConsumer.as_asgi()),
]
