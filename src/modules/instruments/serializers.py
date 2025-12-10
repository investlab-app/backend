from typing import TYPE_CHECKING

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.instruments.models import Instrument
from modules.prices.serializers import PriceDailySummarySerializer

if TYPE_CHECKING:
    from modules.investors.models import Investor


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
            "description_pl",
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
    is_watched = serializers.SerializerMethodField()

    class Meta(InstrumentListSerializer.Meta):
        fields = InstrumentListSerializer.Meta.fields + ["price_info", "is_watched"]

    @extend_schema_field(PriceDailySummarySerializer)
    def get_price_info(self, obj: Instrument):
        # Prefer a pre-fetched snapshot map in context to avoid N calls
        snapshot_map: dict | None = self.context.get("snapshot_map")
        if snapshot_map is None:
            raise serializers.ValidationError("Serializer context missing snapshot_map")

        ticker = obj.ticker.upper()

        return PriceDailySummarySerializer(
            snapshot_map.get(ticker), context=self.context
        ).data

    def get_is_watched(self, obj: Instrument) -> bool:
        investor: Investor | None = self.context.get("investor")
        if not investor:
            return False
        return investor.watching_instruments.filter(id=obj.id).exists()


class InstrumentNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = ["ticker"]


class AllTickersSerializer(serializers.Serializer):
    tickers = serializers.ListField(child=serializers.CharField())
