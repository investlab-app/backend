from django.urls import path

from modules.orders.views import CreateMarketOrderView, DestroyOrderView, ListOrderView

urlpatterns = [
    path("market/", CreateMarketOrderView.as_view()),
    path("cancel/<str:id>", DestroyOrderView.as_view()),
    path("", ListOrderView.as_view()),
]
