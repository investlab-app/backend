from django.urls import path

from modules.investors.views import (
    AccountValueOverTimeView,
    CurrentInvestorView,
    DepositMoneyView,
    InvestorDetailView,
    WatchedInstrumentView,
    WatchedTickersListView,
)

app_name = "investors"

urlpatterns = [
    path("me/", CurrentInvestorView.as_view(), name="current-investor"),
    path(
        "me/account-value/",
        AccountValueOverTimeView.as_view(),
        name="account-value-over-time",
    ),
    path(
        "me/watched-tickers/",
        WatchedTickersListView.as_view(),
        name="watched-tickers",
    ),
    path(
        "me/watched-instruments/<str:instrument_id>/",
        WatchedInstrumentView.as_view(),
        name="watched-instrument",
    ),
    path("deposit/", DepositMoneyView.as_view(), name="deposit"),
    path("<str:clerk_id>/", InvestorDetailView.as_view(), name="investor-detail"),
]
