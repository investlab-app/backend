from django.contrib import admin
from modules.authentication import urls
from modules.core import urls
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


from modules.core.views import StatusView

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/status/", StatusView.as_view(), name="status"),
    # Docs
    path("api/schema/", SpectacularAPIView.as_view(authentication_classes=[],), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", authentication_classes=[],), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema", authentication_classes=[],), name="redoc"),
    # Modules
    path("api/prices/", include("modules.prices.urls")),
    path("api/auth/", include("modules.authentication.urls")),
    path("api/test/", include("modules.core.urls")),
]
