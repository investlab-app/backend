from datetime import datetime
from decimal import Decimal

from django.db.models import Count, Sum

from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.prices.repositories import PolygonPricesRepository
from modules.statistics.schemas import TransactionStats
from modules.transactions.models import Transaction


class TransactionStatsService:
    def __init__(self, prices_service: PolygonPricesRepository | None = None):
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
                total_price=Sum("price"),
                count=Count("id"),
            )
            sell_stats = transactions.filter(is_buy=False).aggregate(
                total_volume=Sum("volume"),
                total_price=Sum("price"),
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
            gain_percentage = (
                (gain / initial_value) * 100 if initial_value != 0 else None
            )
            if gain_percentage is not None and gain_percentage > 999.99:
                gain_percentage = Decimal("999.99")

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
                    gain_percentage=gain_percentage,
                )
            )

        return stats
