from django.contrib import admin
from modules.core import urls
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny  # Added import
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from modules.core.views import HealthCheckView
from modules.authentication.views import ClerkUsernamePasswordSignInView  # Added import

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/healthcheck/", HealthCheckView.as_view(), name="healthcheck"),
    # Docs
    path("api/schema/", SpectacularAPIView.as_view(authentication_classes=[], permission_classes=[AllowAny]), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema", authentication_classes=[], permission_classes=[AllowAny]), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema", authentication_classes=[], permission_classes=[AllowAny]), name="redoc"),
    # Authentication
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/auth/token-refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("api/auth/clerk-signin/", ClerkUsernamePasswordSignInView.as_view(), name="clerk-username-password-signin"),  # Added new URL
    # Modules
    path("api/", include("modules.prices.urls")),
    path("api/", include("modules.core.urls")),
]
