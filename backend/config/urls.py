import logging

from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from modules.core.views import StatusView
from modules.sse.sse_consumer_impl import SSEConsumerImpl
from modules.sse.views import SSESubscribeView, SSEUnsubscribeView

API_PREFIX = "api"

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

sse_urlpatterns = [
    re_path(f"^{API_PREFIX}/sse/?$", SSEConsumerImpl.as_asgi()),
]

urlpatterns = [
    path(
        f"{API_PREFIX}/sse/subscribe", SSESubscribeView.as_view(), name="sse-subscribe"
    ),
    path(
        f"{API_PREFIX}/sse/unsubscribe",
        SSEUnsubscribeView.as_view(),
        name="sse-unsubscribe",
    ),
    path(f"{API_PREFIX}/admin/", admin.site.urls),
    path(f"{API_PREFIX}/status/", StatusView.as_view(), name="status"),
    # Docs
    path(
        f"{API_PREFIX}/schema/",
        SpectacularAPIView.as_view(authentication_classes=[]),
        name="schema",
    ),
    path(
        f"{API_PREFIX}/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=[],
        ),
        name="swagger",
    ),
    path(
        f"{API_PREFIX}/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
            authentication_classes=[],
        ),
        name="redoc",
    ),
    # Modules
    path(f"{API_PREFIX}/prices/", include("modules.prices.urls")),
    path(f"{API_PREFIX}/instruments/", include("modules.instruments.urls")),
    path(f"{API_PREFIX}/auth/", include("modules.authentication.urls")),
    path(f"{API_PREFIX}/test/", include("modules.core.urls")),
]
