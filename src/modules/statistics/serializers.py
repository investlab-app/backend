from rest_framework import serializers


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


class CurrentAccountValueSerializer(serializers.Serializer):
    # InvestorStatsService.get_total_value
    total_account_value = serializers.FloatField()

    # TransactionStats.gain
    gain = serializers.FloatField()

    # TransactionStats.gain_percentage
    gain_percentage = serializers.FloatField(allow_null=True)


class AssetAllocationQueryParams(serializers.Serializer):
    instruments_number = serializers.IntegerField(
        required=False,
        min_value=3,
        max_value=30,
        default=5,
        help_text="Number of top instruments without `Other` position",
    )


class AssetAllocationItemSerializer(serializers.Serializer):
    instrument_name = serializers.CharField(max_length=255)
    instrument_ticker = serializers.CharField(max_length=20)
    instrument_logo = serializers.ImageField(allow_null=True)
    instrument_icon = serializers.ImageField(allow_null=True)

    # AssetAllocation.total_value
    value = serializers.FloatField()

    # AssetAllocation.percentage
    percentage = serializers.FloatField()


class AssetAllocationSerializer(serializers.Serializer):
    # Aggregate AssetAllocation.total_value
    total_value = serializers.FloatField()

    # TransactionStats.gain
    total_gain_this_year = serializers.FloatField()

    allocations = AssetAllocationItemSerializer(many=True)


class OwnedShareSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    symbol = serializers.CharField(max_length=10)

    # AssetAllocation.asset.volume
    volume = serializers.FloatField()

    # AssetAllocation.total_value
    value = serializers.FloatField()

    # TransactionStats.gain
    gain = serializers.FloatField()

    # TransactionStats.gain_percentage
    gain_percentage = serializers.FloatField(allow_null=True)


# stats
class TradingOverviewSerializer(serializers.Serializer):
    # TransactionStats.buy_transactions + TransactionStats.sell_transactions
    total_trades = serializers.IntegerField()

    # TransactionStats.buy_transactions
    buys = serializers.IntegerField()

    # TransactionStats.sell_transactions
    sells = serializers.IntegerField()

    # TransactionStats.gain
    total_gain = serializers.FloatField()


# stats
class MostTradedItemSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10)

    # TransactionStats.buy_transactions + TransactionStats.sell_transactions
    no_trades = serializers.IntegerField()

    # TransactionStats.buy_transactions
    buys = serializers.IntegerField()

    # TransactionStats.sell_transactions
    sells = serializers.IntegerField()

    # TransactionStats.avg_gain
    avg_gain = serializers.FloatField()

    # TransactionStats.avg_loss
    avg_loss = serializers.FloatField()


class TransactionHistoryQueryParams(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=["open", "closed", "both"],
        required=False,
        default="both",
        help_text="Type of positions to fetch: 'open', 'closed', or 'both'",
    )
    tickers = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        max_length=50,
        help_text="List of ticker symbols to fetch prices for (max 50).",
    )


class HistoryEntrySerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(help_text="Date of the transaction")

    quantity = serializers.DecimalField(
        max_digits=20, decimal_places=5, help_text="Number of shares traded"
    )

    final_transaction_value = serializers.FloatField(
        help_text="Value of the transaction at closing or current market price"
    )

    final_share_price = serializers.FloatField(
        help_text="Price per share at the time of sell transaction "
        "or current market price"
    )

    initial_share_price = serializers.FloatField(
        help_text="Price per share at the time of buy transaction"
    )

    gain = serializers.FloatField(help_text="Gain or loss from this transaction")

    gain_percentage = serializers.FloatField(
        help_text="Gain or loss percentage from this transaction"
    )


class PositionSerializer(serializers.Serializer):
    symbol = serializers.CharField(max_length=10, help_text="Ticker symbol")

    name = serializers.CharField(max_length=255, help_text="Instrument name")

    icon = serializers.ImageField(allow_null=True)

    quantity = serializers.DecimalField(
        max_digits=20, decimal_places=5, help_text="Total quantity of shares"
    )

    value = serializers.FloatField(
        help_text="Current market value for open positions or total sell value"
        "for closed positions"
    )

    gain = serializers.FloatField(help_text="Total gain or loss")

    gain_percentage = serializers.FloatField(
        help_text="Total gain or loss percentage"
    )

    history = HistoryEntrySerializer(many=True, help_text="Transaction history")
