from dataclasses import asdict

from rest_framework import serializers

from modules.instruments_v3.models import Instrument


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
            # "icon_url",
            # "logo_url"
        ]
