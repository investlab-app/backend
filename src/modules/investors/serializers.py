from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.instruments.models import Instrument
from modules.investors.models import (
    AccountValueSnapshot,
    Asset,
    DepositHistory,
    Investor,
    NotificationHistory,
)


class InvestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = [
            "id",
            "clerk_id",
            "balance",
            "blocked_funds",
            "language",
            "watching_instruments",
        ]
        read_only_fields = ["id", "clerk_id", "balance"]


class InvestorUpdateSerializer(serializers.ModelSerializer):
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


class WatchedTickersTickerSerializer(serializers.Serializer):
    is_watched = serializers.BooleanField(
        help_text="Whether the instrument is now being watched"
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


class WatchedTickerSerializer(serializers.ModelSerializer):
    """Serializer for watched tickers with icon and ticker information."""

    class Meta:
        model = Instrument
        fields = ["ticker", "name", "icon", "logo"]


class DepositMoneySerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )


class DepositHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositHistory
        fields = ["id", "amount", "deposited_at"]
        read_only_fields = fields


class NotificationHistorySerializer(serializers.ModelSerializer):
    """Serializer for NotificationHistory model."""

    type = serializers.CharField(help_text="Type of the notification")
    message_en = serializers.CharField(help_text="Notification message in English")
    message_pl = serializers.CharField(help_text="Notification message in Polish")
    sent_at = serializers.DateTimeField(help_text="When the notification was sent")

    class Meta:
        model = NotificationHistory
        fields = [
            "id",
            "type",
            "message_en",
            "message_pl",
            "sent_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "sent_at", "created_at", "updated_at"]
