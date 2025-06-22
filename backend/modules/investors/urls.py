from django.urls import path

from modules.investors.views import (
    CurrentInvestorView,
    InvestorDetailView,
    InvestorListCreateView,
)

app_name = "investors"

urlpatterns = [
    path("", InvestorListCreateView.as_view(), name="investor-list-create"),
    path("<int:pk>/", InvestorDetailView.as_view(), name="investor-detail"),
    path("me/", CurrentInvestorView.as_view(), name="current-investor"),
]
