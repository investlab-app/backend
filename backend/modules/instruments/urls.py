from django.urls import path

from modules.instruments.views import (
    InstrumentsListView,
    InstrumentsRetrieveView,
    InstrumentsWithPriceInfoListView,
)

urlpatterns = [
    path("", InstrumentsListView.as_view(), name="instruments-list"),
    path("detail/", InstrumentsRetrieveView.as_view(), name="instrument-detail"),
    path(
        "with-price-info/",
        InstrumentsWithPriceInfoListView.as_view(),
        name="instruments-with-price-info",
    ),
]
