from django.urls import path

from .views import (
    PriceAlertDetailView,
    PriceAlertListCreateView,
    VapidPublicKeyView,
)

app_name = "notifications"

urlpatterns = [
    path(
        "price-alert/",
        PriceAlertListCreateView.as_view(),
        name="price-alert-list-create",
    ),
    path(
        "price-alert/<uuid:pk>/",
        PriceAlertDetailView.as_view(),
        name="price-alert-detail",
    ),
    path(
        "vapid-public-key/",
        VapidPublicKeyView.as_view(),
        name="vapid-public-key",
    ),
]
