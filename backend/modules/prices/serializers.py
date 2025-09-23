from rest_framework import serializers
from rest_framework_dataclasses.serializers import DataclassSerializer

from config.settings import ACCEPTABLE_DATETIME_FORMATS
from modules.prices.constants import POLYGON_INTERVALS
from modules.prices.schemas import PriceBar, PriceDailySummary


class PriceBarsQueryParams(serializers.Serializer):
    ticker = serializers.CharField(required=True, max_length=6)
    start_date = serializers.DateTimeField(
        required=True, input_formats=ACCEPTABLE_DATETIME_FORMATS
    )
    end_date = serializers.DateTimeField(
        input_formats=ACCEPTABLE_DATETIME_FORMATS, default="2025-09-23T00:00:00Z"
    )
    interval = serializers.ChoiceField(choices=POLYGON_INTERVALS)
    interval_multiplier = serializers.IntegerField(default=1, min_value=1)

    def validate(self, attrs):
        if attrs["start_date"] >= attrs["end_date"]:
            raise serializers.ValidationError("Start date must be before end date")
        return super().validate(attrs)


class PricesListQueryParams(serializers.Serializer):
    tickers = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False,
        max_length=50,
        help_text="List of ticker symbols to fetch prices for (max 50).",
    )


class PriceBarSerializer(DataclassSerializer):
    class Meta:
        dataclass = PriceBar


class PriceDailySummarySerializer(DataclassSerializer):
    class Meta:
        dataclass = PriceDailySummary
