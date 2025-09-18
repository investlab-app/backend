from django.urls import path

from modules.investors.views import (
    AccountValueOverTimeView,
    AssetAllocationView,
    CurrentAccountValueView,
    CurrentInvestorView,
    InvestorDetailView,
    InvestorListView,
    InvestorStatsView,
    MostTradedOverviewView,
    OwnedSharesView,
    ProfileOverviewView,
    TradingOverviewView,
)

app_name = "investors"

urlpatterns = [
    path("", InvestorListView.as_view(), name="investor-list-create"),
    path("me/", CurrentInvestorView.as_view(), name="current-investor"),
    path("me/stats/", InvestorStatsView.as_view(), name="investor-stats"),
    path(
        "me/account-value/",
        AccountValueOverTimeView.as_view(),
        name="account-value-over-time",
    ),
    path(
        "me/current-account-value/",
        CurrentAccountValueView.as_view(),
        name="current-account-value",
    ),
    path(
        "me/asset-allocation/",
        AssetAllocationView.as_view(),
        name="asset-allocation",
    ),
    path("me/owned-shares/", OwnedSharesView.as_view(), name="owned-shares"),
    path(
        "me/statistics/most-traded/",
        MostTradedOverviewView.as_view(),
        name="most-traded",
    ),
    path(
        "me/statistics/profile-overview/",
        ProfileOverviewView.as_view(),
        name="profile-overview",
    ),
    path(
        "me/statistics/trading-overview/",
        TradingOverviewView.as_view(),
        name="trading-overview",
    ),
    path("<str:clerk_id>/", InvestorDetailView.as_view(), name="investor-detail"),
]
