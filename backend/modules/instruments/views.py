from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, filters
from rest_framework.request import Request
from rest_framework.response import Response

from modules.instruments.serializers import (
    InstrumentInfoSerializer,
    InstrumentDetailSerializer
)
from modules.instruments.services import InstrumentServiceV2
from modules.instruments.models import Instrument

class InstrumentV2ListView(generics.ListAPIView):
    class _InstrumentListPagination(PageNumberPagination):
        page_size = 100
        page_size_query_param = 'page_size'
        max_page_size = 1000

    queryset = Instrument.objects.all()
    serializer_class = InstrumentInfoSerializer
    pagination_class = _InstrumentListPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ticker']
    ordering_fields = ['ticker']


class InstrumentV2DetailView(generics.RetrieveAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentDetailSerializer
    lookup_field = 'ticker'

    def get_object(self):
        uppercase_ticker = self.kwargs.get(self.lookup_field, '').upper()
        return generics.get_object_or_404(self.get_queryset(), **{self.lookup_field: uppercase_ticker})

class InstrumentPullView(generics.GenericAPIView):
    def get(self, request: Request) -> Response:
        return Response(InstrumentServiceV2.pull_all_instruments())