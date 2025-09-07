from django.urls import path

from modules.investors.views import (
    AccountValueOverTimeView,
    AssetAllocationView,
    CurrentAccountValueView,
    CurrentInvestorView,
    InvestorDetailView,
    InvestorListView,
    InvestorStatsView,
    OwnedSharesView,
    AssetListView,
)

app_name = "investors"

urlpatterns = [
    path("", InvestorListView.as_view(), name="investor-list-create"),
    path("me/", CurrentInvestorView.as_view(), name="current-investor"),
    path("<str:clerk_id>/", InvestorDetailView.as_view(), name="investor-detail"),
    path("me/stats/", InvestorStatsView.as_view(), name="investor-stats"),
    path(
        "balance-history/",
        AccountValueOverTimeView.as_view(),
        name="account-value-over-time",
    ),
    path(
        "balance/",
        CurrentAccountValueView.as_view(),
        name="current-account-value",
    ),
    path(
        "me/asset-allocation/",
        AssetAllocationView.as_view(),
        name="asset-allocation",
    ),
    path("me/owned-shares/", OwnedSharesView.as_view(), name="owned-shares"),
    path("me/assets/", AssetListView.as_view(), name="assets"),
]
