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
    todays_return = serializers.FloatField(help_text="Today's return in currency")

    # TransactionStats.gain
    total_return = serializers.FloatField(help_text="Total return in currency")

    # TransactionStats.total_buy_price
    invested = serializers.FloatField(help_text="Total amount invested")

    # InvestorStatsService.get_total_value
    total_value = serializers.FloatField(help_text="Total account value")


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


class CurrentAccountValueSerializer(serializers.Serializer):
    # InvestorStatsService.get_total_value
    total_account_value = serializers.FloatField()

    # TransactionStats.gain
    gain = serializers.FloatField()

    # IDK yet
    gain_percent = serializers.FloatField()


class AssetAllocationItemSerializer(serializers.Serializer):
    instrument_name = serializers.CharField(max_length=255)
    instrument_ticker = serializers.CharField(max_length=20)
    instrument_logo = serializers.URLField(allow_null=True)
    instrument_icon = serializers.URLField(allow_null=True)

    # AssetAllocation.total_value
    value = serializers.FloatField()

    # AssetAllocation.percentage
    percentage = serializers.FloatField()


class AssetAllocationSerializer(serializers.Serializer):
    # Aggregate AssetAllocation.total_value
    total_value = serializers.FloatField()

    # TransactionStats.gain
    total_return_this_year = serializers.FloatField()

    allocations = AssetAllocationItemSerializer(many=True)


class OwnedShareSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    symbol = serializers.CharField(max_length=10)

    # AssetAllocation.asset.volume
    volume = serializers.FloatField()

    # AssetAllocation.total_value
    value = serializers.FloatField()

    # TransactionStats.gain
    profit = serializers.FloatField()

    # IDK yet
    profit_percentage = serializers.FloatField()


# Not yet implemented
class ProfileOverviewSerializer(serializers.Serializer):
    level = serializers.CharField(max_length=30)
    exp_points = serializers.IntegerField()
    left_to_next_level = serializers.IntegerField()


# stats
class TradingOverviewSerializer(serializers.Serializer):
    # TransactionStats.buy_transactions + TransactionStats.sell_transactions
    total_trades = serializers.IntegerField()

    # TransactionStats.buy_transactions
    buys = serializers.IntegerField()

    # TransactionStats.sell_transactions
    sells = serializers.IntegerField()

    # What are these?
    avg_gain = serializers.FloatField()
    avg_loss = serializers.FloatField()

    # TransactionStats.gain
    total_return = serializers.FloatField()


# stats
class MostTradedItemSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)

    # TransactionStats.buy_transactions + TransactionStats.sell_transactions
    no_trades = serializers.IntegerField()

    # TransactionStats.buy_transactions
    buys = serializers.IntegerField()

    # TransactionStats.sell_transactions
    sells = serializers.IntegerField()

    # What are these?
    avg_gain = serializers.FloatField()
    avg_loss = serializers.FloatField()

    # TransactionStats.gain
    total_return = serializers.FloatField()


class TransactionHistoryQueryParams(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=["open", "closed", "both"],
        required=False,
        default="both",
        help_text="Type of positions to fetch: 'open', 'closed', or 'both'",
    )
    ticker = serializers.CharField(
        required=False, max_length=10, help_text="Filter by specific ticker symbol"
    )


class HistoryEntrySerializer(serializers.Serializer):
    # Transaction.transaction_time
    date = serializers.DateTimeField(help_text="Date of the transaction")

    # Transaction.is_buy
    type = serializers.CharField(
        max_length=10, help_text="Transaction type: BUY or SELL"
    )

    # Transaction.volume
    quantity = serializers.IntegerField(help_text="Number of shares traded")

    # Transaction.transaction_price / Transaction.volume
    share_price = serializers.FloatField(
        help_text="Price per share at the time of transaction"
    )

    # Transaction.transaction_price
    acquisition_price = serializers.FloatField(
        allow_null=True, help_text="Acquisition price (null for SELL transactions)"
    )

    # Prices.???
    market_value = serializers.FloatField(help_text="Current market value")

    # Impossible to calculate
    gain_loss = serializers.FloatField(help_text="Gain or loss amount")
    gain_loss_pct = serializers.FloatField(help_text="Gain or loss percentage")


class PositionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=10, help_text="Ticker symbol")

    # AssetAllocation.asset.volume
    quantity = serializers.IntegerField(help_text="Total quantity of shares")

    # Prices.???
    market_value = serializers.FloatField(help_text="Current market value")

    # TransactionStats.gain
    gain_loss = serializers.FloatField(help_text="Total gain or loss")

    # IDK yet
    gain_loss_pct = serializers.FloatField(help_text="Total gain or loss percentage")

    history = HistoryEntrySerializer(many=True, help_text="Transaction history")


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ["ticker", "volume"]
