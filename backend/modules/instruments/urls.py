from django.urls import path

from modules.instruments.views import (
    InstrumentPullView,
    InstrumentV2DetailView,
    InstrumentV2ListView,
)

urlpatterns = [
    path("pull/", InstrumentPullView.as_view(), name="instruments-pull"),
    path("", InstrumentV2ListView.as_view(), name="instruments-list"),
    path(
        "<str:ticker>/", InstrumentV2DetailView.as_view(), name="instrumentsv2-detail"
    ),
]
