from drf_spectacular.utils import extend_schema
from rest_framework.generics import GenericAPIView

from modules.transactions.serializers import TransactionSerializer


class ListTransactionsView(GenericAPIView):
    @extend_schema(responses={200: TransactionSerializer})
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
