from rest_framework import serializers

from modules.investors.models import Investor


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

    todays_return = serializers.FloatField(help_text="Today's return in currency")
    total_return = serializers.FloatField(help_text="Total return in currency")
    invested = serializers.FloatField(help_text="Total amount invested")
    total_value = serializers.FloatField(help_text="Total account value")


class AccountValueDataSerializer(serializers.Serializer):
    """Serializer for individual account value data point."""

    date = serializers.DateField(help_text="Date of the value measurement")
    value = serializers.FloatField(help_text="Account value on this date")


class AccountValueOverTimeSerializer(serializers.Serializer):
    """Serializer for account value over time data."""

    data = AccountValueDataSerializer(
        many=True, help_text="List of account value data points"
    )


class CurrentAccountValueSerializer(serializers.Serializer):
    total_account_value = serializers.FloatField()
    gain = serializers.FloatField()
    gain_percent = serializers.FloatField()


class AssetAllocationItemSerializer(serializers.Serializer):
    asset_class_display_name = serializers.CharField(max_length=100)
    value = serializers.FloatField()
    percentage = serializers.FloatField()


class AssetAllocationSerializer(serializers.Serializer):
    total_value = serializers.FloatField()
    total_return_this_year = serializers.FloatField()
    allocations = AssetAllocationItemSerializer(many=True)


class OwnedShareItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    symbol = serializers.CharField(max_length=10)
    volume = serializers.FloatField()
    value = serializers.FloatField()
    profit = serializers.FloatField()
    profit_percentage = serializers.FloatField()


class OwnedSharesSerializer(serializers.Serializer):
    owned_shares = OwnedShareItemSerializer(many=True)


class ProfileOverviewSerializer(serializers.Serializer):
    level = serializers.CharField(max_length=30)
    exp_points = serializers.IntegerField()
    left_to_next_level = serializers.IntegerField()


class TradingOverviewSerializer(serializers.Serializer):
    total_trades = serializers.IntegerField()
    buys = serializers.IntegerField()
    sells = serializers.IntegerField()
    avg_gain = serializers.FloatField()
    avg_loss = serializers.FloatField()
    total_return = serializers.FloatField()


class MostTradedItemSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)
    no_trades = serializers.IntegerField()
    buys = serializers.IntegerField()
    sells = serializers.IntegerField()
    avg_gain = serializers.FloatField()
    avg_loss = serializers.FloatField()
    total_return = serializers.FloatField()


class MostTradedOverviewSerializer(serializers.Serializer):
    instruments = MostTradedItemSerializer(many=True)
