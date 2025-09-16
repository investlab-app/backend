from drf_spectacular.utils import extend_schema
from rest_framework import status, views
from rest_framework.response import Response

from modules.markets.repositories import PolygonMarketsRepository
from modules.markets.serializers import (
    MarketHolidaySerializer,
    MarketStatusSerializer,
)


class MarketHolidaysListView(views.APIView):
    @extend_schema(
        responses=MarketHolidaySerializer(many=True),
        description="Retrieve a list of upcoming market holidays.",
    )
    def get(self, request, *args, **kwargs):
        repository = PolygonMarketsRepository()
        holidays = repository.list_market_holidays()

        if holidays is None:
            return Response(
                "Failed to fetch market holidays.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = MarketHolidaySerializer(holidays, many=True)
        return Response(serializer.data)


class MarketStatusView(views.APIView):
    @extend_schema(
        responses=MarketStatusSerializer,
        description="Retrieve the current trading status of the markets and exchanges.",
    )
    def get(self, request, *args, **kwargs):
        repository = PolygonMarketsRepository()
        status_data = repository.get_market_status()

        if status_data is None:
            return Response(
                "Failed to fetch market status.",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = MarketStatusSerializer(status_data)
        return Response(serializer.data)
