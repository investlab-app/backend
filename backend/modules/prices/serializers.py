from datetime import datetime
from decimal import Decimal

from rest_framework import serializers

from modules.core import defaults
from modules.core.utils import get_local_datetime, quantize_decimal
from modules.prices.constants import POLYGON_INTERVALS

MAX_DIGITS = 30
DECIMAL_PLACES = 15
ACCEPTABLE_DATE_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d_%H:%M:%S"]


class PriceBarsQueryParams(serializers.Serializer):
    ticker = serializers.CharField(required=True, max_length=6)
    start_date = serializers.DateTimeField(
        required=True, input_formats=ACCEPTABLE_DATE_FORMATS
    )
    end_date = serializers.DateTimeField(
        input_formats=ACCEPTABLE_DATE_FORMATS,
        default=get_local_datetime().strftime(ACCEPTABLE_DATE_FORMATS[0]),
    )
    interval = serializers.ChoiceField(choices=POLYGON_INTERVALS)
    interval_multiplier = serializers.IntegerField(default=1, min_value=1)

    def validate(self, attrs):
        if attrs["start_date"] >= attrs["end_date"]:
            raise serializers.ValidationError("Start date must be before end date")
        return super().validate(attrs)


class PriceBarSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    high = defaults.DecimalField()
    low = defaults.DecimalField()
    open = defaults.DecimalField()
    close = defaults.DecimalField()

    @staticmethod
    def sanitize_output(record: dict) -> dict:
        for key, value in record.items():
            if isinstance(value, Decimal):
                record[key] = quantize_decimal(value, places=DECIMAL_PLACES)
        return record


class DailySummarySerializer(serializers.Serializer):
    open = defaults.DecimalField()
    high = defaults.DecimalField()
    low = defaults.DecimalField()
    close = defaults.DecimalField()
    volume = serializers.IntegerField()
    volume_weighted_average_price = defaults.DecimalField()

    @staticmethod
    def sanitize_output(record: dict) -> dict:
        for key, value in record.items():
            if isinstance(value, float):
                record[key] = quantize_decimal(Decimal(value), places=DECIMAL_PLACES)
            elif isinstance(value, Decimal):
                record[key] = quantize_decimal(value, places=DECIMAL_PLACES)
        return record


class PriceSerializer(serializers.Serializer):
    current_price = defaults.DecimalField()
    daily_summary = DailySummarySerializer()
    todays_change = defaults.DecimalField()
    todays_change_percent = defaults.DecimalField()
    last_updated = serializers.DateTimeField()

    @staticmethod
    def sanitize_output(record: dict) -> dict:
        for key, value in record.items():
            if isinstance(value, float):
                record[key] = quantize_decimal(Decimal(value), places=DECIMAL_PLACES)
            elif isinstance(value, Decimal):
                record[key] = quantize_decimal(value, places=DECIMAL_PLACES)

        if record.get("daily_summary"):
            record["daily_summary"] = DailySummarySerializer.sanitize_output(
                record["daily_summary"]
            )

        if record.get("last_updated"):
            nanoseconds_in_second = 1e9
            record["last_updated"] = datetime.fromtimestamp(
                record["last_updated"] / nanoseconds_in_second
            )

        return record


class PricesListQueryParams(serializers.Serializer):
    tickers = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False,
        max_length=50,
        help_text="List of ticker symbols to fetch prices for (max 50).",
    )
    include_otc = serializers.BooleanField(required=False, default=False)


class PriceListSerializer(PriceSerializer):
    ticker = serializers.CharField()
