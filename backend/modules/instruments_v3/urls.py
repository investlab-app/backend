from django.urls import path

from modules.instruments_v3.views import InstrumentsListView

urlpatterns = [
    path("", InstrumentsListView.as_view(), name="instruments-list"),
    # path(
    #     "<str:pk>/", InstrumentDetailView.as_view(), name="instrumentsv2-detail"
    # ),
]
