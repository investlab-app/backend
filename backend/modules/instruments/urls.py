from django.urls import path

from modules.instruments.views import (
    InstrumentDetailView,
    InstrumentNewsView,
    InstrumentsAvailableView,
    InstrumentsListView,
)

urlpatterns = [
    path(
        "available/",
        InstrumentsAvailableView.as_view(),
        name="instruments-available",
    ),
    path(
        "",
        InstrumentsListView.as_view(),
        name="instruments-list",
    ),
    path(
        "<str:ticker>/",
        InstrumentDetailView.as_view(),
        name="instrument-detail",
    ),
    path(
        "<str:ticker>/news/",
        InstrumentNewsView.as_view(),
        name="instrument-news",
    ),
]
