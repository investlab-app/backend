from django.urls import path

from modules.investors.views import (
    AccountValueOverTimeView,
    CurrentInvestorView,
    InvestorDetailView,
    InvestorListCreateView,
    InvestorStatsView,
)

app_name = "investors"

urlpatterns = [
    path("", InvestorListCreateView.as_view(), name="investor-list-create"),
    path("<int:pk>/", InvestorDetailView.as_view(), name="investor-detail"),
    path("me/", CurrentInvestorView.as_view(), name="current-investor"),
    path("me/stats/", InvestorStatsView.as_view(), name="investor-stats"),
    path(
        "me/account-value/",
        AccountValueOverTimeView.as_view(),
        name="account-value-over-time",
    ),
]
