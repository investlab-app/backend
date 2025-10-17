from django.urls import path

from modules.investors.views import (
    AccountValueOverTimeView,
    AssetAllocationView,
    CurrentAccountValueView,
    CurrentInvestorView,
    InvestorDetailView,
    InvestorStatsView,
    LanguageUpdateView,
    MostTradedOverviewView,
    OwnedSharesView,
    ProfileOverviewView,
    TradingOverviewView,
    TransactionHistoryView,
)

app_name = "investors"

urlpatterns = [
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
        "me/statistics/profile-overview/",
        ProfileOverviewView.as_view(),
        name="profile-overview",
    ),
    path(
        "me/statistics/trading-overview/",
        TradingOverviewView.as_view(),
        name="trading-overview",
    ),
    path(
        "me/statistics/most-traded/",
        MostTradedOverviewView.as_view(),
        name="most-traded",
    ),
    path(
        "me/transactions-history/",
        TransactionHistoryView.as_view(),
        name="transactions-history",
    ),
    path(
        "me/language/",
        LanguageUpdateView.as_view(),
        name="language-update",
    ),
    path("<str:clerk_id>/", InvestorDetailView.as_view(), name="investor-detail"),
]
