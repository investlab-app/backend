from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Any

from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.prices.services import LatestPriceService
from modules.transactions.models import Transaction

getcontext().prec = 28


@dataclass
class BuyLot:
    volume: Decimal
    price: Decimal
    timestamp: Any = None


@dataclass
class SellDetail:
    volume: Decimal
    sell_price: Decimal
    cost_basis: Decimal
    gain: Decimal
    gain_pct: Decimal | None


@dataclass
class TransactionDetails:
    sells: list[SellDetail]
    remaining_lots_lifo_order: list[dict[str, Any]]
    remaining_lots_fifo_order: list[dict[str, Any]]


@dataclass
class TransactionStats:
    realized_gain: Decimal
    unrealized_gain: Decimal
    total_gain: Decimal
    total_buy_cost: Decimal
    total_gain_pct: Decimal | None
    current_price: Decimal
    remaining_volume: Decimal
    details: TransactionDetails


class TransactionStatsService:
    def __init__(
        self,
        transactions: Iterable[Transaction],
        ticker: str,
        lastest_price_service: LatestPriceService | None = None,
    ):
        self.transactions = sorted(transactions, key=lambda t: t.timestamp)
        self.ticker = ticker
        self.lastest_price_service = lastest_price_service or LatestPriceService()

    @classmethod
    def from_investor_and_instrument(
        cls, investor: Investor, instrument: Instrument
    ) -> "TransactionStatsService":
        qs = Transaction.objects.filter(investor=investor, ticker=instrument).order_by(
            "timestamp"
        )
        return cls(qs, ticker=instrument.ticker)

    def _get_current_price(self, current_price: Decimal | None = None) -> Decimal:
        if current_price is not None:
            return current_price
        prices = self.lastest_price_service.get_prices_default_dict()
        return prices[self.ticker]

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
        current_price: Decimal,
        sell_details: list[SellDetail],
    ) -> TransactionStats:
        remaining_volume = sum(i.volume for i in buy_lots)
        unrealized_gain = sum(i.volume * (current_price - i.price) for i in buy_lots)
        total_gain = realized_gain + unrealized_gain
        total_gain_pct = total_gain / total_buy_cost if total_buy_cost else None

        remaining_lifo_order = [
            {
                "volume": i.volume,
                "buy_price": i.price,
                "contribution": i.volume * (current_price - i.price),
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
            unrealized_gain=unrealized_gain,  # type: ignore
            total_gain=total_gain,
            total_buy_cost=total_buy_cost,
            total_gain_pct=total_gain_pct,
            current_price=current_price,
            remaining_volume=remaining_volume,  # type: ignore
            details=details,
        )

    def _compute_from_transactions(
        self,
        transactions: Iterable[Transaction],
        initial_buy_lots: Iterable[BuyLot] | Sequence[BuyLot],
        current_price: Decimal,
    ) -> TransactionStats:
        buy_lots = [BuyLot(i.volume, i.price, i.timestamp) for i in initial_buy_lots]
        realized_gain = Decimal(0)
        total_buy_cost = sum(i.volume * i.price for i in buy_lots)
        sell_details: list[SellDetail] = []

        for tx in transactions:
            vol, price = tx.volume, tx.price
            if tx.is_buy:
                buy_lots.append(BuyLot(vol, price, tx.timestamp))
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
            total_buy_cost,  # type: ignore
            current_price,
            sell_details,
        )

    def compute_stats(self, current_price: Decimal | None = None) -> TransactionStats:
        current_price = self._get_current_price(current_price)
        return self._compute_from_transactions(
            transactions=self.transactions,
            initial_buy_lots=[],
            current_price=current_price,
        )

    def compute_stats_in_period(
        self, start: datetime, end: datetime, current_price: Decimal | None = None
    ) -> TransactionStats:
        current_price = self._get_current_price(current_price)

        # Calculate state before the period, but with price = 0 to get only buy_lots
        pre_txs = [t for t in self.transactions if t.timestamp < start]
        pre_stats = self._compute_from_transactions(pre_txs, [], Decimal(0))

        # Recreate BuyLot instances from pre_stats
        pre_lots = [
            BuyLot(volume=i["volume"], price=i["buy_price"])
            for i in pre_stats.details.remaining_lots_fifo_order
        ]

        # Process transactions within the window
        window_txs = [t for t in self.transactions if start <= t.timestamp <= end]

        return self._compute_from_transactions(
            transactions=window_txs,
            initial_buy_lots=pre_lots,
            current_price=current_price,
        )
