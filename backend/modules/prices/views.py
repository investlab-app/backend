from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.prices.serializers import (
    InstrumentPriceResponseSerializer,
    InstrumentV2PriceQueryParams,
    PriceInfoResponseSerializer,
)
from modules.prices.services import PricesV2Service


class PricesV2View(generics.GenericAPIView):
    serializer_class = InstrumentPriceResponseSerializer

    @extend_schema(parameters=[InstrumentV2PriceQueryParams])
    def get(self, request: Request) -> Response:
        params = InstrumentV2PriceQueryParams(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = PricesV2Service.get_ohlc(**params.validated_data)
        serializer = InstrumentPriceResponseSerializer(many=True, data=data)
        serializer.is_valid(raise_exception=True)
        json_data = serializer.validated_data
        return Response(json_data)

    def get_serializer(self, *args, **kwargs):
        kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)


class PricesInfoView(generics.GenericAPIView):
    serializer_class = PriceInfoResponseSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        ticker = self.kwargs.get("ticker")
        data = PricesV2Service.get_price_info(ticker)
        sanitized_data = PriceInfoResponseSerializer.sanitize_output(data)
        serializer = PriceInfoResponseSerializer(data=sanitized_data)
        serializer.is_valid(raise_exception=True)
        json_data = serializer.validated_data
        return Response(json_data)
