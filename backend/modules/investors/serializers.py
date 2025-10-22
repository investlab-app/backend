from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.investors.models import AccountValueSnapshot, Asset, Investor


class InvestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = [
            "id",
            "clerk_id",
            "watching_instruments",
        ]
        read_only_fields = ["id", "clerk_id"]


class InvestorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = [
            "id",
            "clerk_id",
            "language",
            "watching_instruments",
        ]
        read_only_fields = ["id", "clerk_id"]


class LanguageUpdateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=[("en", "English"), ("pl", "Polski")],
        help_text="Language code (e.g., 'en', 'pl')",
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
