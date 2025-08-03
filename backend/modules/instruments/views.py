from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.instruments.serializers import (
    InstrumentInfoSerializer,
    InstrumentDetailSerializer
)
from modules.instruments.services import InstrumentServiceV2
from modules.instruments.models import Instrument


class HeheXD(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class InstrumentV2ListView(generics.ListAPIView):
    # That's my recommendation to limit tickers, it still returns around 4k of them
    # queryset = Instrument.objects.exclude(icon_url__isnull=True).exclude(market_cap__isnull=True)

    queryset = Instrument.objects.all()
    serializer_class = InstrumentInfoSerializer
    pagination_class = HeheXD

class InstrumentV2DetailView(generics.RetrieveAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentDetailSerializer
    lookup_field = 'ticker'

class InstrumentPullView(generics.GenericAPIView):
    def get(self, request: Request) -> Response:
        InstrumentServiceV2.pull_all_instruments()
        return Response("done")
