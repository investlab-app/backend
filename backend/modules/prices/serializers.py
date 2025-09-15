from datetime import datetime
from decimal import Decimal

from rest_framework import serializers

from modules.core import defaults
from modules.core.utils import get_local_datetime, quantize_decimal
from modules.prices.constants import POLYGON_INTERVALS

MAX_DIGITS = 30
DECIMAL_PLACES = 15


class InstrumentV2PriceQueryParams(serializers.Serializer):
    ticker = serializers.CharField(required=True, max_length=6)
    start_date = serializers.DateTimeField(
        required=True, input_formats=["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d_%H:%M:%S"]
    )
    end_date = serializers.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d_%H:%M:%S"],
        default=get_local_datetime().strftime("%Y-%m-%dT%H:%M:%S"),
    )
    interval = serializers.ChoiceField(choices=POLYGON_INTERVALS)
    interval_multiplier = serializers.IntegerField(default=1, min_value=1)

    def validate(self, attrs):
        if attrs["start_date"] >= attrs["end_date"]:
            raise serializers.ValidationError("Start date must be before end date")
        return super().validate(attrs)


class InstrumentPriceResponseSerializer(serializers.Serializer):
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


class PriceInfoResponseSerializer(serializers.Serializer):
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


class FullMarketSnapshotQueryParams(serializers.Serializer):
    tickers = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=(
            "Comma separated list of tickers. Empty or omitted means all tickers."
        ),
    )
    include_otc = serializers.BooleanField(required=False, default=False)

    def get_tickers_list(self) -> list[str] | None:
        tickers_str: str | None = self.validated_data.get("tickers")
        if tickers_str is None or tickers_str.strip() == "":
            return None
        return [t.strip().upper() for t in tickers_str.split(",") if t.strip()]


class TickerPriceInfoSerializer(PriceInfoResponseSerializer):
    ticker = serializers.CharField()
