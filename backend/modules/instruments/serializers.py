from decimal import Decimal

from rest_framework import serializers

from modules.core.utils import quantize_decimal

MAX_DIGITS = 30
DECIMAL_PLACES = 15


class InstrumentsListQueryParams(serializers.Serializer):
    tickers = serializers.CharField(
        required=True,
        help_text="Comma-separated list of ticker symbols (e.g., 'AAPL,MSFT,GOOG').",
    )
    page = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text="Page number for pagination.",
    )
    page_size = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=100,
        help_text="Number of items per page (max 100).",
    )
    sort_by = serializers.CharField(
        required=False,
        default=None,
        help_text="Field to sort by (e.g., 'market_cap', 'current_price', 'ticker').",
    )
    sort_direction = serializers.ChoiceField(
        required=False,
        default="asc",
        choices=["asc", "desc"],
        help_text="Sort direction ('asc' or 'desc').",
    )
    sector = serializers.CharField(
        required=False,
        default=None,
        help_text="Filter by sector.",
    )
    industry = serializers.CharField(
        required=False,
        default=None,
        help_text="Filter by industry.",
    )


class InstrumentInfoSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    name = serializers.CharField()
    currency = serializers.CharField()
    current_price = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    previous_close = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    day_change = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    day_change_percent = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    market_cap = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    volume = serializers.IntegerField(allow_null=True)
    sector = serializers.CharField(allow_null=True)
    industry = serializers.CharField(allow_null=True)
    country = serializers.CharField(allow_null=True)

    @staticmethod
    def sanitize_output(record: dict) -> dict:
        for key, value in record.items():
            if isinstance(value, Decimal):
                record[key] = quantize_decimal(value, places=DECIMAL_PLACES)
        return record


class InstrumentDetailedInfoSerializer(InstrumentInfoSerializer):
    description = serializers.CharField(allow_null=True)
    website = serializers.URLField(allow_null=True)
    logo_url = serializers.URLField(allow_null=True)
    exchange = serializers.CharField(allow_null=True)
    fifty_two_week_low = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    fifty_two_week_high = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    trailing_pe = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    forward_pe = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    dividend_yield = serializers.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    earnings_date = serializers.DateTimeField(allow_null=True)
    business_summary = serializers.CharField(allow_null=True)
    financial_data = serializers.JSONField(allow_null=True)
    major_holders = serializers.JSONField(allow_null=True)
    institutional_holders = serializers.ListField(
        child=serializers.DictField(), allow_null=True
    )
    analyst_recommendations = serializers.JSONField(allow_null=True)


class PaginatedInstrumentsResponseSerializer(serializers.Serializer):
    items = InstrumentInfoSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    num_pages = serializers.IntegerField()
