from django.urls import path

from modules.prices.views import PricesInfoView, PricesV2View

urlpatterns = [
    path(
        "ohlc/",
        PricesV2View.as_view(),
        name="prices",
    ),
    path("<str:ticker>/", PricesInfoView.as_view(), name="prices-ticker"),
]
