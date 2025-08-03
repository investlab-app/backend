from rest_framework.pagination import PageNumberPagination
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.instruments.serializers import (
    InstrumentV2InfoSerializer,
    InstrumentV2DetailSerializer
)
from modules.instruments.services import InstrumentServiceV2
from modules.instruments.models import InstrumentV2


class HeheXD(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class InstrumentV2ListView(generics.ListAPIView):
    queryset = InstrumentV2.objects.exclude(icon_url__isnull=True).exclude(market_cap__isnull=True)
    serializer_class = InstrumentV2InfoSerializer
    pagination_class = HeheXD

class InstrumentV2DetailView(generics.RetrieveAPIView):
    queryset = InstrumentV2.objects.all()
    serializer_class = InstrumentV2DetailSerializer
    lookup_field = 'ticker'

class InstrumentPullView(generics.GenericAPIView):
    def get(self, request: Request) -> Response:
        InstrumentServiceV2.pull_all_instruments()
        return Response("done")
