from django.urls import path

from modules.transactions.views import ListTransactionsView

urlpatterns = [path("", ListTransactionsView.as_view())]
