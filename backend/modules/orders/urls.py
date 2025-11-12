from django.urls import path

from modules.orders.views import (
    DestroyOrderView,
    LimitOrderView,
    ListOrderView,
    MarketOrderView,
)

urlpatterns = [
    path("market/", MarketOrderView.as_view(), name="market-orders"),
    path("limit/", LimitOrderView.as_view(), name="limit-orders"),
    path("cancel/<str:id>", DestroyOrderView.as_view(), name="destroy-order"),
    path("", ListOrderView.as_view(), name="list-orders"),
]
