from django.urls import path

from modules.prices.views import PricesView

urlpatterns = [
    path(
        "prices/",
        PricesView.as_view(),
        name="prices",
    ),
]
