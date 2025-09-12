from django.urls import path
from modules.markets.views import MarketHolidaysListView, MarketStatusView

urlpatterns = [
    path("holidays/", MarketHolidaysListView.as_view(), name="market-holidays"),
    path("status/", MarketStatusView.as_view(), name="market-status"),
]
