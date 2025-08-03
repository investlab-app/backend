from decimal import Decimal

from rest_framework import serializers

from modules.core.utils import get_local_datetime, quantize_decimal
from modules.core import defaults
from modules.prices.constants import POLYGON_INTERVALS

MAX_DIGITS = 30
DECIMAL_PLACES = 15

class InstrumentV2PriceQueryParams(serializers.Serializer):
    ticker = serializers.CharField(required = True, max_length=6)
    start_date = serializers.DateTimeField(required=True, input_formats=["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d_%H:%M:%S"])
    end_date = serializers.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d_%H:%M:%S"],
        default=get_local_datetime().strftime("%Y-%m-%dT%H:%M:%S")
    )
    interval = serializers.ChoiceField(choices=POLYGON_INTERVALS)
    interval_multiplier = serializers.IntegerField(default = 1, min_value=1)

    def validate(self, attrs):
        if attrs['start_date'] > attrs['end_date']:
            raise serializers.ValidationError('Start date must be before end date')

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
