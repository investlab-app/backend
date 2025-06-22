from decimal import Decimal

from rest_framework import serializers

from modules.core.utils import get_local_datetime, quantize_decimal

MAX_DIGITS = 30
DECIMAL_PLACES = 15


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
    high = serializers.DecimalField(
        max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES
    )
    low = serializers.DecimalField(max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES)
    open = serializers.DecimalField(
        max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES
    )
    close = serializers.DecimalField(
        max_digits=MAX_DIGITS, decimal_places=DECIMAL_PLACES
    )

    @staticmethod
    def sanitize_output(record: dict) -> dict:
        for key, value in record.items():
            if isinstance(value, Decimal):
                record[key] = quantize_decimal(value, places=DECIMAL_PLACES)
        return record
