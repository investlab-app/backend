from django.urls import path

from modules.prices.views import (
    FullMarketSnapshotView,
    PricesInfoView,
    PricesV2View,
)

urlpatterns = [
    path(
        "ohlc/",
        PricesV2View.as_view(),
        name="prices",
    ),
    path(
        "full-market-snapshot/",
        FullMarketSnapshotView.as_view(),
        name="full-market-snapshot",
    ),
    path("<str:ticker>/", PricesInfoView.as_view(), name="prices-ticker"),
]
