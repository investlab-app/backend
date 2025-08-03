from django.urls import path

from modules.instruments.views import (
    InstrumentDetailView,
    InstrumentNewsView,
    InstrumentsAvailableView,
    InstrumentsListView,
    InstrumentV2ListView,
    InstrumentV2DetailView,
    InstrumentPullView
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
        'pull/',
        InstrumentPullView.as_view(),
        name="instruments-pull"
    ),
    path(
        'instrumetv2/',
        InstrumentV2ListView.as_view(),
        name="instrumentsv2-list"
    ),
    path(
        'instrumetv2/<str:ticker>/',
        InstrumentV2DetailView.as_view(),
        name="instrumentsv2-detail"
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
