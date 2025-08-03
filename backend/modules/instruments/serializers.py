from decimal import Decimal

from rest_framework import serializers

from modules.core.utils import quantize_decimal
from modules.instruments.models import InstrumentV2

MAX_DIGITS = 30
DECIMAL_PLACES = 15


class InstrumentsListQueryParams(serializers.Serializer):
    tickers = serializers.CharField(
        required=False,
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

class InstrumentV2InfoSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    ticker_type = serializers.CharField()
    delisted = serializers.BooleanField()
    icon_url = serializers.URLField()

    market_cap = serializers.DecimalField(
        max_digits=30, decimal_places=15
    )
    currency_name = serializers.CharField()
    sector = serializers.CharField()

class InstrumentV2DetailSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    ticker_type = serializers.CharField()

    delisted = serializers.BooleanField()

    description = serializers.CharField()
    icon_url = serializers.URLField()
    logo_url = serializers.URLField()
    homepage_url = serializers.URLField()

    currency_name = serializers.CharField()
    market = serializers.CharField()
    market_cap = serializers.DecimalField(
        max_digits=30, decimal_places=15
    )
    phone_number = serializers.CharField()
    sector = serializers.CharField()
    total_employess = serializers.IntegerField

    @staticmethod
    def sanitize_output(record: dict) -> dict:
        for key, value in record.items():
            if isinstance(value, Decimal):
                record[key] = quantize_decimal(value, places=DECIMAL_PLACES)
        return record





    

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




class AddressSerializer(serializers.Serializer):
    """
    Serializer for the 'address' object within the Ticker Overview.
    """
    address1 = serializers.CharField(source='address', required=False, allow_null=True)
    address2 = serializers.CharField(required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_null=True)
    postal_code = serializers.CharField(required=False, allow_null=True)
    state = serializers.CharField(required=False, allow_null=True)

class BrandingSerializer(serializers.Serializer):
    """
    Serializer for the 'branding' object within the Ticker Overview.
    """
    icon_url = serializers.URLField(required=False, allow_null=True)
    logo_url = serializers.URLField(required=False, allow_null=True)

class TickerOverviewResultSerializer(serializers.Serializer):
    """
    Serializer for the 'results' object, which contains the core ticker details.
    """
    active = serializers.BooleanField(default=True)
    address = AddressSerializer(required=False, allow_null=True)
    branding = BrandingSerializer(required=False, allow_null=True)
    cik = serializers.CharField(required=False, allow_null=True)
    composite_figi = serializers.CharField(required=False, allow_null=True)
    currency_name = serializers.CharField()
    delisted_utc = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    homepage_url = serializers.URLField(required=False, allow_null=True)
    list_date = serializers.DateField(required=False, allow_null=True)
    locale = serializers.CharField()
    market = serializers.CharField()
    market_cap = serializers.DecimalField(max_digits=30, decimal_places=15, required=False, allow_null=True)
    name = serializers.CharField()
    phone_number = serializers.CharField(required=False, allow_null=True)
    primary_exchange = serializers.CharField(required=False, allow_null=True)
    round_lot = serializers.IntegerField(required=False, allow_null=True)
    share_class_figi = serializers.CharField(required=False, allow_null=True)
    share_class_shares_outstanding = serializers.DecimalField(max_digits=20, decimal_places=0, required=False, allow_null=True)
    sic_code = serializers.CharField(required=False, allow_null=True)
    sic_description = serializers.CharField(required=False, allow_null=True)
    ticker = serializers.CharField()
    ticker_root = serializers.CharField(required=False, allow_null=True)
    ticker_suffix = serializers.CharField(required=False, allow_null=True)
    total_employees = serializers.IntegerField(required=False, allow_null=True)
    type = serializers.CharField(required=False, allow_null=True)
    weighted_shares_outstanding = serializers.DecimalField(max_digits=20, decimal_places=0, required=False, allow_null=True) 

    def create(self, validated_data):
        kwargs = dict(validated_data)
        kwargs['delisted'] = not kwargs['active']
        if "branding" in validated_data and validated_data['branding'] is not None:
            kwargs.update(validated_data["branding"])
        if kwargs["description"] is None:
            kwargs["description"] = "No description"

        # Discard unnecessary fields
        model_fields = [f.name for f in InstrumentV2._meta.get_fields()]
        kwargs = {k: v for k, v in kwargs.items() if k in model_fields} 

        return InstrumentV2.objects.create(**kwargs)

class TestSerializer(serializers.Serializer):
    something = serializers.CharField(source='example.value')