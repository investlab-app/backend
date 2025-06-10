from django.urls import path, re_path

from modules.instruments.views import InstrumentDetailView, InstrumentNewsView, InstrumentsListView, InstrumentsAvailableView

urlpatterns = [
    path(
        "instruments/available/",
        InstrumentsAvailableView.as_view(),
        name="instruments-available",
    ),
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
    path(
        "instruments/<str:ticker>/news/",
        InstrumentNewsView.as_view(),
        name="instrument-news",
    ),
]
