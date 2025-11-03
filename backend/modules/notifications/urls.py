from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import VapidPublicKeyView, NotificationViewSet

app_name = "notifications"

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notification")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "vapid-public-key/",
        VapidPublicKeyView.as_view(),
        name="vapid-public-key",
    ),
]
