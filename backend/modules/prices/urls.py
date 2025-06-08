from django.urls import path
from modules.prices.views import PricesView

urlpatterns = [
    path(
        "",
        PricesView.as_view(),
        name="prices",
    ),
]
