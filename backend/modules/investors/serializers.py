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

    # final_ticker_value - initial_ticker_value + sold_price - bought_price
    todays_return = serializers.FloatField(help_text="Today's return in currency")

    # final_ticker_value + sold_price - bought_price
    total_return = serializers.FloatField(help_text="Total return in currency")

    # bought_price
    invested = serializers.FloatField(help_text="Total amount invested")

    # final_ticker_value + balance
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
    # final_ticker_value + balance
    total_account_value = serializers.FloatField()

    # final_ticker_value + balance - money_received
    gain = serializers.FloatField()

    # (final_ticker_value + balance - money_received) / money_received
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

    # sold_price + final_ticker_value - bought_price
    profit = serializers.FloatField()

    # bought_price / (sold_price + final_ticker_value)
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
    date = serializers.DateTimeField(help_text="Date of the transaction")
    type = serializers.CharField(
        max_length=10, help_text="Transaction type: BUY or SELL"
    )
    quantity = serializers.IntegerField(help_text="Number of shares traded")
    share_price = serializers.FloatField(
        help_text="Price per share at the time of transaction"
    )
    acquisition_price = serializers.FloatField(
        allow_null=True, help_text="Acquisition price (null for SELL transactions)"
    )
    market_value = serializers.FloatField(help_text="Current market value")
    gain_loss = serializers.FloatField(help_text="Gain or loss amount")
    gain_loss_pct = serializers.FloatField(help_text="Gain or loss percentage")


class PositionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=10, help_text="Ticker symbol")
    quantity = serializers.IntegerField(help_text="Total quantity of shares")
    market_value = serializers.FloatField(help_text="Current market value")
    gain_loss = serializers.FloatField(help_text="Total gain or loss")
    gain_loss_pct = serializers.FloatField(help_text="Total gain or loss percentage")
    history = HistoryEntrySerializer(many=True, help_text="Transaction history")
