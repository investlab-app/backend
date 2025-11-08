from django.urls import path

from modules.prices.views import (
    PriceAlertDetailView,
    PriceAlertListCreateView,
    PricesBarsView,
    PricesListView,
    PricesRetrieveView,
)

urlpatterns = [
    path("", PricesListView.as_view(), name="prices-list"),
    path("bars/", PricesBarsView.as_view(), name="prices-bars"),
    path(
        "price-alert/",
        PriceAlertListCreateView.as_view(),
        name="price-alert-list-create",
    ),
    path(
        r"price-alert/<uuid:pk>/",
        PriceAlertDetailView.as_view(),
        name="price-alert-detail",
    ),
    path("<str:ticker>/", PricesRetrieveView.as_view(), name="prices-detail"),
]
