from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Sum
from pydantic import BaseModel

from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.prices.repositories import PolygonPricesRepository
from modules.transactions.models import Transaction


class TransactionParams(BaseModel):
    investor: Investor
    ticker: Instrument
    volume: Decimal
    action_price: Decimal

    class Config:
        arbitrary_types_allowed = True


class ExecuteTransactionService:
    def buy(self, params: TransactionParams):
        transaction_price = params.volume * params.action_price
        if params.investor.balance < transaction_price:
            raise ValueError("Investor doesn't have enough balance")

        params.investor.balance -= transaction_price

        try:
            asset: Asset = Asset.objects.get(  # ty: ignore[invalid-assignment]
                investor=params.investor, ticker=params.ticker
            )
            asset.volume += params.volume
        except ObjectDoesNotExist:
            asset = Asset(
                investor=params.investor, ticker=params.ticker, volume=params.volume
            )

        with transaction.atomic():
            params.investor.save()
            Transaction.objects.create(
                investor=params.investor,
                ticker=params.ticker,
                volume=params.volume,
                price=params.volume * params.action_price,
                is_buy=True,
            )
            asset.save()

    def sell(self, params: TransactionParams):
        try:
            asset: Asset = Asset.objects.get(  # ty: ignore[invalid-assignment]
                investor=params.investor, ticker=params.ticker
            )
        except ObjectDoesNotExist:
            raise ValueError("Asset does not exist.") from None

        if asset.volume < params.volume:
            raise ValueError("Not enough assets to sell.")

        transaction_price = params.volume * params.action_price

        params.investor.balance += transaction_price
        asset.volume -= params.volume

        with transaction.atomic():
            params.investor.save()
            asset.save()
            Transaction.objects.create(
                investor=params.investor,
                ticker=params.ticker,
                volume=params.volume,
                price=transaction_price,
                is_buy=False,
            )


class TransactionStats(BaseModel):
    ticker: str

    total_buy_volume: Decimal
    total_buy_price: Decimal
    total_sell_volume: Decimal
    total_sell_price: Decimal

    initial_ticker_volume: Decimal
    initial_ticker_price: Decimal
    final_ticker_volume: Decimal
    final_ticker_price: Decimal

    buy_transactions: int
    sell_transactions: int

    gain: Decimal


class TransactionStatsService:
    def __init__(self, prices_service=None):
        self.prices_service = prices_service or PolygonPricesRepository()

    def get_stats(
        self,
        investor: Investor,
        tickers: list[Instrument] | None = None,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
    ) -> list[TransactionStats]:
        if tickers is None:
            return []

        stats = []

        initial_prices = {}
        if start_datetime:
            initial_prices = self.prices_service.get_prices_at(tickers, start_datetime)

        final_prices = {}
        if end_datetime:
            final_prices = self.prices_service.get_prices_at(tickers, end_datetime)

        for t in tickers:
            transactions = Transaction.objects.filter(investor=investor, ticker=t)

            initial_ticker_volume = Decimal(0)

            if start_datetime:
                transactions_before_start = Transaction.objects.filter(
                    investor=investor, ticker=t, timestamp__lt=start_datetime
                )
                initial_buy_volume = transactions_before_start.filter(
                    is_buy=True
                ).aggregate(total_volume=Sum("volume"))["total_volume"] or Decimal(0)
                initial_sell_volume = transactions_before_start.filter(
                    is_buy=False
                ).aggregate(total_volume=Sum("volume"))["total_volume"] or Decimal(0)
                initial_ticker_volume = initial_buy_volume - initial_sell_volume

                transactions = transactions.filter(timestamp__gte=start_datetime)
            if end_datetime:
                transactions = transactions.filter(timestamp__lte=end_datetime)

            buy_stats = transactions.filter(is_buy=True).aggregate(
                total_volume=Sum("volume"),
                total_price=Sum("transaction_price"),
                count=Count("id"),
            )
            sell_stats = transactions.filter(is_buy=False).aggregate(
                total_volume=Sum("volume"),
                total_price=Sum("transaction_price"),
                count=Count("id"),
            )

            final_ticker_volume = (
                initial_ticker_volume
                + (buy_stats["total_volume"] or 0)
                - (sell_stats["total_volume"] or 0)
            )

            initial_price = initial_prices.get(t, 0)
            initial_value = initial_price * initial_ticker_volume
            final_price = final_prices.get(t, 0)
            final_value = final_price * final_ticker_volume
            total_buy_price = buy_stats["total_price"] or 0
            total_sell_price = sell_stats["total_price"] or 0

            gain = final_value + total_sell_price - total_buy_price - initial_value

            stats.append(
                TransactionStats(
                    ticker=t.ticker,
                    total_buy_volume=buy_stats["total_volume"] or Decimal(0),
                    total_buy_price=buy_stats["total_price"] or Decimal(0),
                    buy_transactions=buy_stats["count"] or 0,
                    total_sell_volume=sell_stats["total_volume"] or Decimal(0),
                    total_sell_price=sell_stats["total_price"] or Decimal(0),
                    sell_transactions=sell_stats["count"] or 0,
                    initial_ticker_price=initial_prices.get(t, 0),
                    initial_ticker_volume=initial_ticker_volume,
                    final_ticker_price=final_prices.get(t, 0),
                    final_ticker_volume=final_ticker_volume,
                    gain=gain,
                )
            )

        return stats
