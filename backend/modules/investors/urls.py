from django.urls import path

from modules.investors.views import (
    AccountValueOverTimeView,
    CurrentInvestorView,
    InvestorDetailView,
    LanguageUpdateView,
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
        "me/language/",
        LanguageUpdateView.as_view(),
        name="language-update",
    ),
    path("<str:clerk_id>/", InvestorDetailView.as_view(), name="investor-detail"),
]
