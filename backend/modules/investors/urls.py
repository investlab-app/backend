from django.urls import path

from modules.investors.views import (
    AccountValueOverTimeView,
    CurrentInvestorView,
    InvestorDetailView,
    InvestorListView,
)

app_name = "investors"

urlpatterns = [
    path("", InvestorListView.as_view(), name="investor-list"),
    path("me/", CurrentInvestorView.as_view(), name="current-investor"),
    path(
        "me/account-value/",
        AccountValueOverTimeView.as_view(),
        name="account-value-over-time",
    ),
    path("<str:clerk_id>/", InvestorDetailView.as_view(), name="investor-detail"),
]
