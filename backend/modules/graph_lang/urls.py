from django.urls import path

from modules.graph_lang.views import ListCreateGraphView, RetrieveUpdateDestroyGraphView, RunGraphView

urlpatterns = [
    path("", ListCreateGraphView.as_view(), name="graph-list-create"),
    path("<str:pk>/run/", RunGraphView.as_view(), name="graph-run"),
    path("<str:pk>/", RetrieveUpdateDestroyGraphView.as_view(), name="graph-detail"),
]
