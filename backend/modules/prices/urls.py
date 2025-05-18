from django.urls import path

from modules.prices.views import PricesView

urlpatterns = [
    # Shuffle urls
    path(
        "prices/",
        PricesView.as_view(),
        name="prices",
    ),
]
