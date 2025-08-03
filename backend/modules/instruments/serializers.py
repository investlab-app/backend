from decimal import Decimal

from rest_framework import serializers

from modules.core.utils import quantize_decimal
from modules.instruments.models import InstrumentV2

MAX_DIGITS = 30
DECIMAL_PLACES = 15


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