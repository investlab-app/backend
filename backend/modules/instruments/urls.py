from django.urls import path

from modules.instruments.views import (
    InstrumentV2ListView,
    InstrumentV2DetailView,
    InstrumentPullView
)

urlpatterns = [
    path(
        'pull/',
        InstrumentPullView.as_view(),
        name="instruments-pull"
    ),
    path(
        '',
        InstrumentV2ListView.as_view(),
        name="instruments-list"
    ),
    path(
        '<str:ticker>/',
        InstrumentV2DetailView.as_view(),
        name="instrumentsv2-detail"
    ),
]
