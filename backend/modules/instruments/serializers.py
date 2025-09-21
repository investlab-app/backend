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


class InstrumentWithPriceSerializer(InstrumentListSerializer):
    price_info = serializers.SerializerMethodField()

    class Meta(InstrumentListSerializer.Meta):
        fields = InstrumentListSerializer.Meta.fields + ["price_info"]

    def get_price_info(self, obj: Instrument):
        # Prefer a pre-fetched snapshot map in context to avoid N calls
        snapshot_map: dict | None = self.context.get("snapshot_map")
        if not snapshot_map:
            raise serializers.ValidationError("Serializer context missing snapshot_map")

        ticker = obj.ticker.upper()
        return snapshot_map.get(ticker).dict() if ticker in snapshot_map else None
