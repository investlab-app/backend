from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.investors.models import AccountValueSnapshot, Asset, Investor


class InvestorSerializer(serializers.ModelSerializer):
    watching_instruments_count = serializers.IntegerField(
        source="watching_instruments.count", read_only=True
    )

    class Meta:
        model = Investor
        fields = [
            "clerk_id",
            "watching_instruments",
            "watching_instruments_count",
        ]
        read_only_fields = ["clerk_id"]


class InvestorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = ["watching_instruments"]


class InvestorListQueryParams(serializers.Serializer):
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


class InvestorStatsSerializer(serializers.Serializer):
    """Serializer for investor statistics data."""

    # TransactionStats.gain
    todays_gain = serializers.FloatField(help_text="Today's gain in currency")

    # TransactionStats.gain
    total_gain = serializers.FloatField(help_text="Total gain in currency")

    # TransactionStats.total_buy_price
    invested = serializers.FloatField(help_text="Total amount invested")

    # InvestorStatsService.get_total_value
    total_value = serializers.FloatField(help_text="Total account value")


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["ticker", "volume"]


class AccountValueSnapshotDailySerializer(serializers.ModelSerializer):
    """Serializer for AccountValueSnapshot model."""

    date = serializers.SerializerMethodField(help_text="Date of the value measurement")
    value = serializers.FloatField(help_text="Account value on this date")

    class Meta:
        model = AccountValueSnapshot
        fields = ["date", "value"]

    @extend_schema_field(serializers.DateField())
    def get_date(self, obj):
        return obj.timestamp.date()
