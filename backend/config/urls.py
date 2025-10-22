from django.conf import settings
from django.conf.urls.static import static
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
    path("ws/prices/", PriceStreamConsumer.as_asgi()),
    path("ws/prices/<str:names>/", PriceStreamConsumer.as_asgi()),
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
    path(f"{PREFIX}/auth/", include("modules.authentication.urls")),
    path(f"{PREFIX}/instruments/", include("modules.instruments.urls")),
    path(f"{PREFIX}/investors/", include("modules.investors.urls")),
    path(f"{PREFIX}/markets/", include("modules.markets.urls")),
    path(f"{PREFIX}/news/", include("modules.news.urls")),
    path(f"{PREFIX}/prices/", include("modules.prices.urls")),
    path(f"{PREFIX}/test/", include("modules.core.urls")),
    path(f"{PREFIX}/orders/", include("modules.orders.urls")),
    path(f"{PREFIX}/statistics/", include("modules.statistics.urls")),
]

# Consider other media server on production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
