from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from modules.core.views import StatusView
from modules.prices.consumers import PriceStreamConsumer

PREFIX = "api"

websocket_urlpatterns = [
    path(r"ws/prices/<str:names>", PriceStreamConsumer.as_asgi()),
]

urlpatterns = [
    path(f"{PREFIX}/admin/", admin.site.urls),
    path(f"{PREFIX}/status/", StatusView.as_view(), name="status"),
    # Docs
    path(
        f"{PREFIX}/schema/",
        SpectacularAPIView.as_view(authentication_classes=[]),
        name="schema",
    ),
    path(
        f"{PREFIX}/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=[],
        ),
        name="swagger",
    ),
    path(
        f"{PREFIX}/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
            authentication_classes=[],
        ),
        name="redoc",
    ),
    # Modules
    path(f"{PREFIX}/prices/", include("modules.prices.urls")),
    path(f"{PREFIX}/instruments/", include("modules.instruments.urls")),
    path(f"{PREFIX}/auth/", include("modules.authentication.urls")),
    path(f"{PREFIX}/investors/", include("modules.investors.urls")),
    path(f"{PREFIX}/test/", include("modules.core.urls")),
]
