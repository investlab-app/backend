from django.urls import path

from .views import VapidPublicKeyView

app_name = "notifications"

urlpatterns = [
    path(
        "vapid-public-key/",
        VapidPublicKeyView.as_view(),
        name="vapid-public-key",
    ),
]
