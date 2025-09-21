from django.urls import path

from modules.prices.views import (
    PricesBarsView,
    PricesListView,
    PricesRetrieveView,
)

urlpatterns = [
    path("", PricesListView.as_view(), name="prices-list"),
    path("bars/", PricesBarsView.as_view(), name="prices-bars"),
    path("<str:ticker>/", PricesRetrieveView.as_view(), name="prices-detail"),
]
