from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from modules.core.views import HealthCheckView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthcheck/", HealthCheckView.as_view(), name="healthcheck"),
    # Docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Authentication
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token-refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Modules
]
