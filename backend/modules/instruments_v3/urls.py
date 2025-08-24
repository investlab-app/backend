from django.urls import path

from modules.instruments_v3.views import InstrumentsListView, InstrumentsRetrieveView

urlpatterns = [
    path("", InstrumentsListView.as_view(), name="instruments-list"),
    path(
        "details/", InstrumentsRetrieveView.as_view(), name="instruments-details"
    ),
]
