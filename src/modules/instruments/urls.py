from django.urls import path

from modules.instruments.views import (
    AllInstrumentsTickers,
    InstrumentsListView,
    InstrumentsRetrieveView,
    InstrumentsWithPricesListView,
)

urlpatterns = [
    path("", InstrumentsListView.as_view(), name="instruments-list"),
    path("tickers/", AllInstrumentsTickers.as_view(), name="instruments-tickers"),
    path("detail/", InstrumentsRetrieveView.as_view(), name="instrument-detail"),
    path(
        "with-prices/",
        InstrumentsWithPricesListView.as_view(),
        name="instruments-with-prices-list",
    ),
]
