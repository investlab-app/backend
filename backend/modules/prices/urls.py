from modules.prices.views import PricesView
from django.urls import path

urlpatterns = [
    # Shuffle urls
    path(
        "prices/",
        PricesView.as_view(),
        name="prices",
    ),
]