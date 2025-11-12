from django.urls import path

from modules.orders.views import (
    CreateLimitOrderView,
    CreateMarketOrderView,
    DestroyOrderView,
    ListOrderView,
)

urlpatterns = [
    path("market/", CreateMarketOrderView.as_view(), name="create-market-order"),
    path("limit/", CreateLimitOrderView.as_view(), name="create-limit-order"),
    path("cancel/<str:id>", DestroyOrderView.as_view(), name="destroy-order"),
    path("", ListOrderView.as_view(), name="list-orders"),
]
