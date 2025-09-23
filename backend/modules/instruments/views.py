from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics
from rest_framework.response import Response

from modules.instruments.models import Instrument
from modules.instruments.serializers import (
    InstrumentListSerializer,
    InstrumentRetrieveSerializer,
    InstrumentWithPriceSerializer,
)
from modules.prices.repositories import PolygonPricesRepository


class InstrumentsListView(generics.ListAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentListSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["ticker"]
    ordering_fields = ["ticker"]


class InstrumentsRetrieveView(generics.GenericAPIView):
    """
    Retrieve an instrument by one of the following query parameters:
    id, ticker, cik, composite_figi, share_class_figi
    """

    queryset = Instrument.objects.all()
    serializer_class = InstrumentRetrieveSerializer
    lookup_fields = ["id", "ticker", "cik", "composite_figi", "share_class_figi"]

    @extend_schema(
        responses=InstrumentRetrieveSerializer,
        parameters=[
            OpenApiParameter(
                name=field,
                description=f"Filter by {field}.",
                required=False,
                location=OpenApiParameter.QUERY,
                type=str,
            )
            for field in lookup_fields
        ],
        description=(
            "Retrieve an instrument by one of the following query parameters: "
            "id, ticker, cik, composite_figi, or share_class_figi. "
            "Provide exactly one of these fields."
        ),
    )
    def get(self, request, *args, **kwargs):
        criteria = {
            field: request.query_params.get(field).upper()
            for field in self.lookup_fields
            if request.query_params.get(field)
        }
        if not criteria or len(criteria) > 1:
            return Response(
                "Please provide exactly one of the following query parameters: "
                "id, ticker, cik, composite_figi, or share_class_figi.",
                status=400,
            )

        instrument = get_object_or_404(self.get_queryset(), **criteria)
        serializer = self.get_serializer(instrument)
        return Response(serializer.data)


class InstrumentsWithPricesListView(generics.ListAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentWithPriceSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["ticker"]
    ordering_fields = ["ticker"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        items = page if page is not None else queryset

        tickers = [obj.ticker.upper() for obj in items]
        repository = PolygonPricesRepository()
        try:
            snapshot_map = repository.get_prices_map(tickers=tickers) or {}
        except Exception:
            snapshot_map = {}

        context = {**self.get_serializer_context(), "snapshot_map": snapshot_map}
        serializer = self.get_serializer(items, many=True, context=context)

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
