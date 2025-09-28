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

    # TransactionStats.gain
    todays_return = serializers.FloatField(help_text="Today's return in currency")

    # TransactionStats.gain
    total_return = serializers.FloatField(help_text="Total return in currency")

    # TransactionStats.total_buy_price
    invested = serializers.FloatField(help_text="Total amount invested")

    # InvestorStatsService.get_total_value
    total_value = serializers.FloatField(help_text="Total account value")


class AccountValueDataSerializer(serializers.Serializer):
    """Serializer for individual account value data point."""

    # AccountValueHistory.date
    date = serializers.DateField(help_text="Date of the value measurement")

    # AccountValueHistory.value
    value = serializers.FloatField(help_text="Account value on this date")


class AccountValueOverTimeSerializer(serializers.Serializer):
    """Serializer for account value over time data."""

    data = AccountValueDataSerializer(
        many=True, help_text="List of account value data points"
    )


class CurrentAccountValueSerializer(serializers.Serializer):
    # InvestorStatsService.get_total_value
    total_account_value = serializers.FloatField()

    # TransactionStats.gain
    gain = serializers.FloatField()

    # IDK yet
    gain_percent = serializers.FloatField()


class AssetAllocationItemSerializer(serializers.Serializer):
    asset_class_display_name = serializers.CharField(max_length=100)

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


class OwnedShareItemSerializer(serializers.Serializer):
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


class OwnedSharesSerializer(serializers.Serializer):
    owned_shares = OwnedShareItemSerializer(many=True)


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


# stats
class MostTradedOverviewSerializer(serializers.Serializer):
    instruments = MostTradedItemSerializer(many=True)


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
