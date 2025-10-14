from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.prices.repositories import PolygonPricesRepository
from modules.prices.serializers import (
    PriceBarSerializer,
    PriceBarsQueryParams,
    PriceDailySummarySerializer,
    PricesListQueryParams,
)


class PricesBarsView(generics.GenericAPIView):
    serializer_class = PriceBarSerializer

    @extend_schema(
        parameters=[PriceBarsQueryParams], responses=PriceBarSerializer(many=True)
    )
    def get(self, request: Request) -> Response:
        params = PriceBarsQueryParams(data=request.query_params)
        params.is_valid(raise_exception=True)
        repository = PolygonPricesRepository()
        price_bars = repository.get_ohlc(**params.validated_data)  # type: ignore[missing-argument]
        serializer = self.get_serializer(instance=price_bars, many=True)
        return Response(serializer.data)


class PricesListView(generics.GenericAPIView):
    serializer_class = PriceDailySummarySerializer

    @extend_schema(parameters=[PricesListQueryParams])
    def get(self, request: Request) -> Response:
        params = PricesListQueryParams(data=request.query_params)
        params.is_valid(raise_exception=True)

        tickers_list = params.validated_data.get("tickers")
        tickers_list = [ticker.upper() for ticker in tickers_list]

        repository = PolygonPricesRepository()
        prices = repository.get_prices(tickers=tickers_list)

        serializer = self.get_serializer(instance=prices, many=True)
        return Response(serializer.data)


class PricesRetrieveView(generics.GenericAPIView):
    serializer_class = PriceDailySummarySerializer

    def get(self, request: Request, ticker: str) -> Response:
        repository = PolygonPricesRepository()
        prices = repository.get_price(ticker=ticker)
        serializer = self.get_serializer(instance=prices)
        return Response(serializer.data)



class PriceAlertListCreateView(generics.ListCreateAPIView):
    serializer_class = PriceAlertSerializer

    def get_queryset(self):
        clerk_id = self.request.user.id
        return PriceAlert.objects.filter(
            investor__clerk_id=clerk_id, is_active=True
        ).select_related("instrument")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PriceAlertCreateSerializer
        return PriceAlertSerializer


class PriceAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PriceAlertSerializer

    def get_queryset(self):
        clerk_id = self.request.user.id
        return PriceAlert.objects.filter(investor__clerk_id=clerk_id)