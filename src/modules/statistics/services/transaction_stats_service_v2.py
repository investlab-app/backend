from collections import UserDict
from collections.abc import Iterable, Sequence
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Any

from pydantic import BaseModel

from modules.core.utils import get_attr
from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.prices.repositories import PolygonPricesRepository
from modules.prices.services import LatestPriceService
from modules.transactions.models import Transaction

getcontext().prec = 28


class BuyLot(BaseModel):
    volume: Decimal
    price: Decimal
    timestamp: Any = None


class SellDetail(BaseModel):
    volume: Decimal
    sell_price: Decimal
    cost_basis: Decimal
    gain: Decimal
    gain_pct: Decimal | None


class TransactionDetails(BaseModel):
    sells: list[SellDetail]
    remaining_lots_lifo_order: list[dict[str, Any]]
    remaining_lots_fifo_order: list[dict[str, Any]]


class TransactionStats(BaseModel):
    realized_gain: Decimal
    unrealized_gain: Decimal
    total_gain: Decimal
    total_buy_cost: Decimal
    total_gain_pct: Decimal | None
    end_period_price: Decimal
    remaining_volume: Decimal
    details: TransactionDetails


class TransactionStatsDict(UserDict[str, TransactionStats]):
    """
    A dictionary-like container for TransactionStats, with utility methods.

    key: str - Ticker symbol
    value: TransactionStats - Statistics for the corresponding ticker
    """

    def __setitem__(self, key: str, value: TransactionStats):
        if not isinstance(value, TransactionStats):
            raise ValueError("Value must be an instance of TransactionStats")
        super().__setitem__(key, value)

    def sum_attribute(self, attribute: str) -> Decimal:
        total = Decimal(0)
        for stats in self.data.values():
            if not hasattr(stats, attribute):
                raise ValueError(f"TransactionStats has no attribute '{attribute}'")
            value = get_attr(stats, attribute)
            total += value
        return total


class TransactionStatsService:
    def __init__(
        self,
        transactions: Iterable[Transaction],
        ticker: str,
        lastest_price_service: LatestPriceService | None = None,
        polygon_prices_repository: PolygonPricesRepository | None = None,
    ):
        self.transactions = sorted(transactions, key=lambda t: t.timestamp)
        self.ticker = ticker
        self.lastest_price_service = lastest_price_service or LatestPriceService()
        self.polygon_prices_repository = (
            polygon_prices_repository or PolygonPricesRepository()
        )

    @classmethod
    def from_investor_and_instrument(
        cls, investor: Investor, instrument: Instrument, **kwargs
    ) -> "TransactionStatsService":
        qs = Transaction.objects.filter(investor=investor, ticker=instrument).order_by(
            "timestamp"
        )
        return cls(qs, ticker=instrument.ticker, **kwargs)

    def _get_current_price(self) -> Decimal:
        prices = self.lastest_price_service.get_prices_default_dict()
        return prices[self.ticker]

    def _get_price_at(self, timestamp: datetime) -> Decimal:
        price = self.polygon_prices_repository.get_price_at(self.ticker, timestamp)
        if price is None:
            raise ValueError(f"Price not found for {self.ticker} at {timestamp}")
            # return Decimal("1")
        return price

    @staticmethod
    def _consume_sell_volume(
        buy_lots: list[BuyLot], sell_volume: Decimal
    ) -> tuple[Decimal, Decimal]:
        """FIFO consumption of existing lots."""
        consumed_cost = Decimal(0)
        consumed_volume = Decimal(0)

        if sum(i.volume for i in buy_lots) < sell_volume:
            raise ValueError("Sell volume exceeds holdings")

        while sell_volume > 0:
            lot = buy_lots[0]
            take = min(lot.volume, sell_volume)
            consumed_cost += take * lot.price
            consumed_volume += take

            lot.volume -= take
            sell_volume -= take

            if lot.volume == 0:
                buy_lots.pop(0)

        return consumed_volume, consumed_cost

    @staticmethod
    def _finalize_stats(
        buy_lots: list[BuyLot],
        realized_gain: Decimal,
        total_buy_cost: Decimal,
        end_period_price: Decimal,
        sell_details: list[SellDetail],
    ) -> TransactionStats:
        remaining_volume = sum((i.volume for i in buy_lots), start=Decimal(0))
        unrealized_gain = sum(
            (i.volume * (end_period_price - i.price) for i in buy_lots),
            start=Decimal(0),
        )
        total_gain = realized_gain + unrealized_gain
        total_gain_pct = total_gain / total_buy_cost if total_buy_cost else None

        remaining_lifo_order = [
            {
                "volume": i.volume,
                "buy_price": i.price,
                "contribution": i.volume * (end_period_price - i.price),
            }
            for i in reversed(buy_lots)
        ]
        details = TransactionDetails(
            sells=sell_details,
            remaining_lots_lifo_order=remaining_lifo_order,
            remaining_lots_fifo_order=[
                {"volume": i.volume, "buy_price": i.price} for i in buy_lots
            ],
        )

        return TransactionStats(
            realized_gain=realized_gain,
            unrealized_gain=unrealized_gain,
            total_gain=total_gain,
            total_buy_cost=total_buy_cost,
            total_gain_pct=total_gain_pct,
            end_period_price=end_period_price,
            remaining_volume=remaining_volume,
            details=details,
        )

    def _compute_from_transactions(
        self,
        transactions: Iterable[Transaction],
        initial_buy_lots: Iterable[BuyLot] | Sequence[BuyLot],
        end_period_price: Decimal,
    ) -> TransactionStats:
        buy_lots = [
            BuyLot(volume=i.volume, price=i.price, timestamp=i.timestamp)
            for i in initial_buy_lots
        ]
        realized_gain = Decimal(0)
        total_buy_cost = sum((i.volume * i.price for i in buy_lots), start=Decimal(0))
        sell_details: list[SellDetail] = []

        for tx in transactions:
            vol, price = tx.volume, tx.price
            if tx.is_buy:
                buy_lots.append(BuyLot(volume=vol, price=price, timestamp=tx.timestamp))
                total_buy_cost += vol * price

            else:  # sell
                consumed_volume, consumed_cost = self._consume_sell_volume(
                    buy_lots, vol
                )
                gain = consumed_volume * price - consumed_cost
                realized_gain += gain
                sell_details.append(
                    SellDetail(
                        volume=consumed_volume,
                        sell_price=price,
                        cost_basis=consumed_cost,
                        gain=gain,
                        gain_pct=(gain / consumed_cost) if consumed_cost else None,
                    )
                )

        return self._finalize_stats(
            buy_lots,
            realized_gain,
            total_buy_cost,
            end_period_price,
            sell_details,
        )

    def compute_stats(self, current_price: Decimal | None = None) -> TransactionStats:
        current_price = current_price or self._get_current_price()
        return self._compute_from_transactions(
            transactions=self.transactions,
            initial_buy_lots=[],
            end_period_price=current_price,
        )

    def compute_stats_in_period(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        end_period_price: Decimal | None = None,
    ) -> TransactionStats:
        """
        Compute stats for transactions inside a time window [start, end].

        If `start` is None, the window starts from the beginning of history.
        If `end` is None, the window goes until the latest transaction.
        If `end_period_price` is None, the price at `end` timestamp is used,
        or the current price if `end` is also None.
        """
        if end_period_price is None:
            if end:
                end_period_price = self._get_price_at(end)
            else:
                end_period_price = self._get_current_price()

        # Calculate state before the period (transactions strictly before `start`),
        # using price=0 so we only get the resulting buy lots (virtual lots).
        if start is None:
            pre_txs: list[Transaction] = []
        else:
            pre_txs = [t for t in self.transactions if t.timestamp < start]

        pre_stats = self._compute_from_transactions(pre_txs, [], Decimal(0))

        # Recreate BuyLot instances from pre_stats (FIFO order)
        pre_lots = [
            BuyLot(volume=i["volume"], price=i["buy_price"])
            for i in pre_stats.details.remaining_lots_fifo_order
        ]

        # Build window transactions according to provided bounds.
        if start is None and end is None:
            window_txs = self.transactions
        elif start is None:
            window_txs = [t for t in self.transactions if t.timestamp <= end]
        elif end is None:
            window_txs = [t for t in self.transactions if t.timestamp >= start]
        else:
            window_txs = [t for t in self.transactions if start <= t.timestamp <= end]

        return self._compute_from_transactions(
            transactions=window_txs,
            initial_buy_lots=pre_lots,
            end_period_price=end_period_price,
        )


class MultipleInstrumentsTransactionStatsService:
    def __init__(
        self,
        investor: Investor,
        instruments: list[Instrument],
        lastest_price_service: LatestPriceService | None = None,
        polygon_prices_repository: PolygonPricesRepository | None = None,
    ):
        self.investor = investor
        self.instruments = instruments
        self.lastest_price_service = lastest_price_service or LatestPriceService()
        self.polygon_prices_repository = (
            polygon_prices_repository or PolygonPricesRepository()
        )
        self.transaction_stats_services: dict[str, TransactionStatsService] = {
            instrument.ticker: TransactionStatsService.from_investor_and_instrument(
                investor=investor,
                instrument=instrument,
                lastest_price_service=self.lastest_price_service,
                polygon_prices_repository=self.polygon_prices_repository,
            )
            for instrument in instruments
        }

    def compute_stats(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> TransactionStatsDict:
        """Compute stats for all instruments, optionally within a time window."""
        stats = TransactionStatsDict()
        if start or end:
            for ticker, service in self.transaction_stats_services.items():
                stats[ticker] = service.compute_stats_in_period(start=start, end=end)
        else:
            for ticker, service in self.transaction_stats_services.items():
                stats[ticker] = service.compute_stats()

        return stats
