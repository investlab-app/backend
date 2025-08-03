from django.urls import path

from modules.prices.views import PricesV2View

urlpatterns = [
    path(
        "ohcl/",
        PricesV2View.as_view(),
        name="prices",
    )
]
