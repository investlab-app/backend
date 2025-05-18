from datetime import datetime, timedelta
from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers
from rest_framework.request import Request
from rest_framework.response import Response

from modules.core.utils import get_local_datetime
from modules.prices.dtos import InstrumentPriceDTO
from modules.prices.services import PricesServiceMinimal


class PricesView(generics.GenericAPIView):
    def __init__(self):
        self._service = PricesServiceMinimal()

    class InstrumentPriceQueryParams(serializers.Serializer):
        ticker = serializers.CharField(
            required=True,
            help_text="A ticker for which a price will be get.",
            max_length=6,
        )
        start_date = serializers.DateTimeField(
            required=True,
            help_text="The starting date and time for the price data.",
            input_formats=["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d_%H:%M:%S"],
        )
        end_date = serializers.DateTimeField(
            required=False,
            help_text="The ending date and time for the price data.",
            default=get_local_datetime().strftime("%Y-%m-%dT%H:%M:%S"),
            input_formats=["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d_%H:%M:%S"],
        )
        interval = serializers.CharField(
            required=False,
            default="1d",
            help_text="The interval for the price data (e.g., 1m, 1h, 1d).",
            max_length=3,
        )

    class InstrumentPriceResponseSerializer(serializers.Serializer):
        timestamp = serializers.DateTimeField()
        ticker = serializers.CharField(max_length=10)
        high = serializers.FloatField()
        low = serializers.FloatField()
        open = serializers.FloatField()
        close = serializers.FloatField()
        volume = serializers.FloatField()

    @extend_schema(
        parameters=[InstrumentPriceQueryParams],
        responses=[InstrumentPriceResponseSerializer(many=True)],
        request=InstrumentPriceQueryParams,
    )
    def get(self, request: Request) -> Response:
        params = self.InstrumentPriceQueryParams(data=request.query_params)
        params.is_valid(raise_exception=True)
        validated = cast(dict, params.validated_data)  # Fix for Pylance type issue

        instrument_data: list[InstrumentPriceDTO] = (
            self._service.get_instrument_price_for_timeperiod(
                validated["ticker"],
                validated["start_date"],
                validated["end_date"],
                validated["interval"],
            )
        )
        serialized = self.InstrumentPriceResponseSerializer(instrument_data, many=True)
        return Response(serialized.data)
