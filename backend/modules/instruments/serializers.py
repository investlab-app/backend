from rest_framework import serializers

from modules.instruments.models import Instrument


class InstrumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = [
            "id",
            "ticker",
            "type",
            "active",
            "name",
            "market",
            "market_cap",
            "currency_name",
            "icon",
            "logo",
        ]


class InstrumentRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = [
            "id",
            "ticker",
            "type",
            "active",
            "name",
            "cik",
            "market",
            "market_cap",
            "composite_figi",
            "currency_name",
            "locale",
            "primary_exchange",
            "share_class_figi",
            "description",
            "ticker_root",
            "ticker_suffix",
            "homepage_url",
            "list_date",
            "phone_number",
            "share_class_shares_outstanding",
            "sic_code",
            "sic_description",
            "total_employees",
            "weighted_shares_outstanding",
            "address",
            "icon",
            "logo",
        ]


class InstrumentNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = ["ticker"]
