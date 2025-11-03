from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.investors.models import AccountValueSnapshot, Asset, Investor


class InvestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = [
            "id",
            "clerk_id",
            "balance",
            "language",
            "watching_instruments",
        ]
        read_only_fields = ["id", "clerk_id", "balance"]


class LanguageUpdateSerializer(serializers.Serializer):
    language = serializers.ChoiceField(
        choices=[("en", "English"), ("pl", "Polski")],
        help_text="Language code (e.g., 'en', 'pl')",
    )


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


class DepositMoneySerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
