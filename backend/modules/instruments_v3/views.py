from django.shortcuts import get_object_or_404
from rest_framework import filters, generics
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from modules.core.pagination import DynamicPageSizePagination
from modules.instruments_v3.models import Instrument
from modules.instruments_v3.serializers import InstrumentListSerializer, InstrumentRetrieveSerializer


class InstrumentsListView(generics.ListAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentListSerializer
    pagination_class = DynamicPageSizePagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["ticker"]
    ordering_fields = ["ticker"]


class InstrumentsRetrieveView(generics.GenericAPIView):
    """
    Retrieve an instrument by one of the following query parameters:
        GET /api/instruments/detail/?id=a9c013ae-8d4d-4f81-b92e-a2f1d348cd3f
        GET /api/instruments/detail/?ticker=APPL
        GET /api/instruments/detail/?cik=0000320193
        GET /api/instruments/detail/?composite_figi=BBG000B9XRY4
        GET /api/instruments/detail/?share_class_figi=BBG001S5N8V8
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
                status=400
            )

        instrument = get_object_or_404(self.get_queryset(), **criteria)
        serializer = self.get_serializer(instrument)
        return Response(serializer.data)
