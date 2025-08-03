from decimal import Decimal

from rest_framework import serializers

from modules.core.utils import quantize_decimal
from modules.instruments.models import Instrument
from modules.core import defaults

class InstrumentInfoSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    ticker_type = serializers.CharField()
    delisted = serializers.BooleanField()
    icon_url = serializers.URLField()

    market_cap = defaults.DecimalField()
    currency_name = serializers.CharField()
    sector = serializers.CharField()

class InstrumentDetailSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    ticker_type = serializers.CharField()

    delisted = serializers.BooleanField()

    description = serializers.CharField()
    icon_url = serializers.URLField()
    logo_url = serializers.URLField()
    homepage_url = serializers.URLField()

    currency_name = serializers.CharField()
    market = serializers.CharField()
    market_cap = defaults.DecimalField()
    phone_number = serializers.CharField()
    sector = serializers.CharField()
    total_employess = serializers.IntegerField

    @staticmethod
    def sanitize_output(record: dict) -> dict:
        for key, value in record.items():
            if isinstance(value, Decimal):
                record[key] = quantize_decimal(value, places=15)
        return record


class AddressSerializer(serializers.Serializer):
    address1 = serializers.CharField(source='address', required=False, allow_null=True)
    address2 = serializers.CharField(required=False, allow_null=True)
    city = serializers.CharField(required=False, allow_null=True)
    postal_code = serializers.CharField(required=False, allow_null=True)
    state = serializers.CharField(required=False, allow_null=True)

class BrandingSerializer(serializers.Serializer):
    icon_url = serializers.URLField(required=False, allow_null=True)
    logo_url = serializers.URLField(required=False, allow_null=True)

class TickerOverviewResultSerializer(serializers.Serializer):
    active = serializers.BooleanField(default=True)
    address = AddressSerializer(required=False, allow_null=True)
    branding = BrandingSerializer()
    cik = serializers.CharField(required=False, allow_null=True)
    composite_figi = serializers.CharField(required=False, allow_null=True)
    currency_name = serializers.CharField()
    delisted_utc = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField()
    homepage_url = serializers.URLField(required=False, allow_null=True)
    list_date = serializers.DateField(required=False, allow_null=True)
    locale = serializers.CharField()
    market = serializers.CharField()
    market_cap = defaults.DecimalField()
    name = serializers.CharField()
    phone_number = serializers.CharField(required=False, allow_null=True)
    primary_exchange = serializers.CharField(required=False, allow_null=True)
    round_lot = serializers.IntegerField(required=False, allow_null=True)
    share_class_figi = serializers.CharField(required=False, allow_null=True)
    share_class_shares_outstanding = defaults.DecimalField(required=False, allow_null=True)
    sic_code = serializers.CharField(required=False, allow_null=True)
    sic_description = serializers.CharField(source='sector')
    ticker = serializers.CharField()
    ticker_root = serializers.CharField(required=False, allow_null=True)
    ticker_suffix = serializers.CharField(required=False, allow_null=True)
    total_employees = serializers.IntegerField(required=False, allow_null=True)
    type = serializers.CharField(source='ticker_type')
    weighted_shares_outstanding = defaults.DecimalField(required=False, allow_null=True) 

    def create(self, validated_data): #TODO: implement object update
        kwargs = dict(validated_data)
        kwargs['delisted'] = not kwargs['active']
        kwargs.update(validated_data["branding"])

        # Discard unnecessary fields
        model_fields = [f.name for f in Instrument._meta.get_fields()]
        kwargs = {k: v for k, v in kwargs.items() if k in model_fields} 

        return Instrument.objects.create(**kwargs)