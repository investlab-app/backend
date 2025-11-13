from django.urls import path

from modules.orders.views import (
    DestroyOrderView,
    LimitOrderView,
    ListOrderView,
    MarketOrderView,
)

urlpatterns = [
    path("market/", MarketOrderView.as_view(), name="market-order"),
    path("limit/", LimitOrderView.as_view(), name="limit-order"),
    path("cancel/<uuid:id>/", DestroyOrderView.as_view(), name="destroy-order"),
    path("", ListOrderView.as_view(), name="list-orders"),
]
