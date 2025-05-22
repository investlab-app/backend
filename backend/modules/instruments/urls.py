from django.urls import path, re_path

from modules.instruments.views import (
    InstrumentDetailView,
    InstrumentsListView,
)


urlpatterns = [
    path(
        "instruments/",
        InstrumentsListView.as_view(),
        name="instruments-list",
    ),
    path(
        "instruments/<str:ticker>/",
        InstrumentDetailView.as_view(),
        name="instrument-detail",
    ),
]
