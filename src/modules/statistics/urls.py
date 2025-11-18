from django.urls import path

from modules.statistics.views import (
    AssetAllocationView,
    CurrentAccountValueView,
    InvestorStatsView,
    MostTradedOverviewView,
    OwnedSharesView,
    TradingOverviewView,
    TransactionHistoryView,
)

app_name = "statistics"

urlpatterns = [
    path("stats/", InvestorStatsView.as_view(), name="investor-stats"),
    path(
        "current-account-value/",
        CurrentAccountValueView.as_view(),
        name="current-account-value",
    ),
    path(
        "asset-allocation/",
        AssetAllocationView.as_view(),
        name="asset-allocation",
    ),
    path("owned-shares/", OwnedSharesView.as_view(), name="owned-shares"),
    path(
        "statistics/trading-overview/",
        TradingOverviewView.as_view(),
        name="trading-overview",
    ),
    path(
        "statistics/most-traded/",
        MostTradedOverviewView.as_view(),
        name="most-traded",
    ),
    path(
        "transactions-history/",
        TransactionHistoryView.as_view(),
        name="transactions-history",
    ),
]
