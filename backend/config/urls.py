from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from modules.core.views import StatusView

API_PREFIX = "api/v1"

urlpatterns = [
    path(f"{API_PREFIX}/admin/", admin.site.urls),
    path(f"{API_PREFIX}/status/", StatusView.as_view(), name="status"),
    # Docs
    path(
        f"{API_PREFIX}/schema/",
        SpectacularAPIView.as_view(
            authentication_classes=[],
        ),
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
    path(f"{API_PREFIX}/auth/", include("modules.authentication.urls")),
    path(f"{API_PREFIX}/test/", include("modules.core.urls")),
]
