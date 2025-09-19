from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.prices.serializers import (
    PricesListQueryParams,
    PriceBarSerializer,
    PriceBarsQueryParams,
    PriceSerializer,
    PriceListSerializer,
)
from modules.prices.services import PricesV2Service


class PricesListView(generics.GenericAPIView):

    @extend_schema(parameters=[PricesListQueryParams])
    def get(self, request: Request, *args, **kwargs) -> Response:
        params = PricesListQueryParams(data=request.query_params)
        params.is_valid(raise_exception=True)

        tickers_list = params.validated_data.get("tickers")
        tickers_list = [ticker.upper() for ticker in tickers_list]
        include_otc = params.validated_data.get("include_otc")

        snapshot_map = PricesV2Service.get_full_market_snapshot(
            tickers=tickers_list, include_otc=include_otc
        )

        # Reshape: { 'AAPL': {...}, ... } -> [ { ticker: 'AAPL', ... }, ... ]
        items = [
            {"ticker": ticker, **info}
            for ticker, info in snapshot_map.items()
        ]

        serializer = PriceListSerializer(many=True, data=items)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class PricesRetrieveView(generics.GenericAPIView):
    serializer_class = PriceSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        ticker = self.kwargs.get("ticker")
        data = PricesV2Service.get_price_info(ticker)
        sanitized_data = PriceSerializer.sanitize_output(data)
        serializer = PriceSerializer(data=sanitized_data)
        serializer.is_valid(raise_exception=True)
        json_data = serializer.validated_data
        return Response(json_data)


class PricesBarsView(generics.GenericAPIView):
    serializer_class = PriceBarSerializer

    @extend_schema(
        parameters=[PriceBarsQueryParams],
        responses=PriceBarsQueryParams(many=True)
    )
    def get(self, request: Request) -> Response:
        params = PriceBarsQueryParams(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = PricesV2Service.get_ohlc(**params.validated_data)
        serializer = PriceBarSerializer(many=True, data=data)
        serializer.is_valid(raise_exception=True)
        json_data = serializer.validated_data
        return Response(json_data)
