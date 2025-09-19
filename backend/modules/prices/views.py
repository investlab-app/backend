from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.prices.serializers import (
    PricesListQueryParams,
    PriceBarSerializer,
    PriceBarsQueryParams,
    PriceSerializer,
    TickerPriceInfoSerializer,
)
from modules.prices.services import PricesV2Service


class PricesListView(generics.GenericAPIView):
    @extend_schema(parameters=[PricesListQueryParams])
    def get(self, request: Request, *args, **kwargs) -> Response:
        params = PricesListQueryParams(data=request.query_params)
        params.is_valid(raise_exception=True)
        tickers_list = params.get_tickers_list()
        include_otc = params.validated_data.get("include_otc", False)

        snapshot_map = PricesV2Service.get_full_market_snapshot(
            tickers=tickers_list, include_otc=include_otc
        )

        # Shape: { 'AAPL': {...}, ... } -> [ { ticker: 'AAPL', ... }, ... ]
        items = [{"ticker": ticker, **info} for ticker, info in snapshot_map.items()]

        serializer = TickerPriceInfoSerializer(many=True, data=items)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "count": len(items),
                "status": "OK",
                "tickers": serializer.validated_data,
            }
        )


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

    @extend_schema(parameters=[PriceBarsQueryParams])
    def get(self, request: Request) -> Response:
        params = PriceBarsQueryParams(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = PricesV2Service.get_ohlc(**params.validated_data)
        serializer = PriceBarSerializer(many=True, data=data)
        serializer.is_valid(raise_exception=True)
        json_data = serializer.validated_data
        return Response(json_data)

    def get_serializer(self, *args, **kwargs):
        kwargs["many"] = True
        return super().get_serializer(*args, **kwargs)
