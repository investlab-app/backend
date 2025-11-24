from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, getcontext
from typing import Any

from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.prices.services import LatestPriceService
from modules.transactions.models import Transaction

# increase precision for financial calculations
getcontext().prec = 28


@dataclass
class BuyLot:
    volume: Decimal
    price: Decimal
    timestamp: Any


class TransactionStatsService:
    def __init__(
        self,
        transactions: Iterable[Any],
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

    def compute_stats(self, current_price: Decimal | None = None) -> dict[str, Any]:
        if current_price is None:
            prices = self.lastest_price_service.get_prices_default_dict()
            current_price = prices[self.ticker]

        buy_lots: list[BuyLot] = []
        realized_gain = Decimal(0)
        total_buy_cost = Decimal(0)
        sell_details: list[dict[str, Any]] = []

        for tx in self.transactions:
            vol, price = tx.volume, tx.price
            if tx.is_buy:
                buy_lots.append(BuyLot(volume=vol, price=price, timestamp=tx.timestamp))
                total_buy_cost += vol * price
            else:
                sell_volume = vol
                if sum(i.volume for i in buy_lots) < sell_volume:
                    raise ValueError(
                        "Sell volume exceeds holdings (short sells not supported)"
                    )
                consumed_cost = Decimal(0)
                consumed_volume = Decimal(0)
                while sell_volume > 0:
                    lot = buy_lots[0]
                    take = min(lot.volume, sell_volume)
                    consumed_cost += take * lot.price
                    consumed_volume += take
                    lot.volume -= take
                    sell_volume -= take
                    if lot.volume == 0:
                        buy_lots.pop(0)
                realized_gain += consumed_volume * price - consumed_cost
                sell_details.append(
                    {
                        "volume": consumed_volume,
                        "sell_price": price,
                        "cost_basis": consumed_cost,
                        "gain": consumed_volume * price - consumed_cost,
                        "gain_pct": (consumed_volume * price - consumed_cost)
                        / consumed_cost
                        if consumed_cost
                        else None,
                    }
                )

        remaining_volume = sum(i.volume for i in buy_lots)
        unrealized_gain = sum(i.volume * (current_price - i.price) for i in buy_lots)
        total_gain = realized_gain + unrealized_gain
        total_gain_pct = total_gain / total_buy_cost if total_buy_cost else None

        return {
            "realized_gain": realized_gain,
            "unrealized_gain": unrealized_gain,
            "total_gain": total_gain,
            "total_buy_cost": total_buy_cost,
            "total_gain_pct": total_gain_pct,
            "current_price": current_price,
            "remaining_volume": remaining_volume,
            "details": {
                "sells": sell_details,
                "remaining_lots_lifo_order": [
                    {
                        "volume": i.volume,
                        "buy_price": i.price,
                        "contribution": i.volume * (current_price - i.price),
                    }
                    for i in reversed(buy_lots)
                ],
                "remaining_lots_fifo_order": [
                    {"volume": i.volume, "buy_price": i.price} for i in buy_lots
                ],
            },
        }

    def compute_stats_in_period(
        self, start: datetime, end: datetime, current_price: Decimal | None = None
    ) -> dict[str, Any]:
        if current_price is None:
            prices = self.lastest_price_service.get_prices_default_dict()
            current_price = prices[self.ticker]

        pre_txs = [t for t in self.transactions if t.timestamp < start]
        pre_service = TransactionStatsService(
            pre_txs,
            ticker=self.ticker,
            lastest_price_service=self.lastest_price_service,
        )
        pre_stats = pre_service.compute_stats(current_price=Decimal(0))

        buy_lots: list[BuyLot] = [
            BuyLot(volume=i['volume'], price=i['buy_price'], timestamp=None)
            for i in pre_stats['details']['remaining_lots_fifo_order']
        ]
        total_buy_cost = sum(i.volume * i.price for i in buy_lots)
        window_txs = [t for t in self.transactions if start <= t.timestamp <= end]
        realized_gain = Decimal(0)
        sell_details: list[dict[str, Any]] = []

        for tx in window_txs:
            vol, price = tx.volume, tx.price
            if tx.is_buy:
                buy_lots.append(BuyLot(volume=vol, price=price, timestamp=tx.timestamp))
                total_buy_cost += vol * price
            else:
                sell_volume = vol
                if sum(i.volume for i in buy_lots) < sell_volume:
                    raise ValueError("Sell volume exceeds holdings for this period.")
                consumed_cost = Decimal(0)
                consumed_volume = Decimal(0)
                while sell_volume > 0:
                    lot = buy_lots[0]
                    take = min(lot.volume, sell_volume)
                    consumed_cost += take * lot.price
                    consumed_volume += take
                    lot.volume -= take
                    sell_volume -= take
                    if lot.volume == 0:
                        buy_lots.pop(0)
                gain = consumed_volume * price - consumed_cost
                realized_gain += gain
                sell_details.append({
                    "volume": consumed_volume,
                    "sell_price": price,
                    "cost_basis": consumed_cost,
                    "gain": gain,
                    "gain_pct": (gain / consumed_cost) if consumed_cost else None,
                })

        remaining_volume = sum(i.volume for i in buy_lots)
        unrealized_gain = sum(i.volume * (current_price - i.price) for i in buy_lots)
        total_gain = realized_gain + unrealized_gain
        total_gain_pct = (total_gain / total_buy_cost) if total_buy_cost else None

        return {
            "realized_gain": realized_gain,
            "unrealized_gain": unrealized_gain,
            "total_gain": total_gain,
            "total_buy_cost": total_buy_cost,
            "total_gain_pct": total_gain_pct,
            "current_price": current_price,
            "remaining_volume": remaining_volume,
            "details": {
                "sells": sell_details,
                "remaining_lots_lifo_order": [
                    {
                        "volume": i.volume,
                        "buy_price": i.price,
                        "contribution": i.volume * (current_price - i.price),
                    }
                    for i in reversed(buy_lots)
                ],
                "remaining_lots_fifo_order": [
                    {"volume": i.volume, "buy_price": i.price} for i in buy_lots
                ],
            },
        }
#
#
# class MultipleInstrumentStatsService:
#     def __init__(
#         self,
#         investor: Investor,
#         instruments: list[Instrument],
#         lastest_price_service: LatestPriceService | None = None,
#     ):
#         self.investor = investor
#         self.instruments = instruments
#         self.lastest_price_service = lastest_price_service or LatestPriceService()
#
#     def get_stats(self) -> dict[str, dict[str, Any]]:
#         stats = {}
#         prices = self.lastest_price_service.get_prices_default_dict()
#         for instrument in self.instruments:
#             svc = TransactionStatsService.from_investor_and_instrument(
#                 self.investor, instrument
#             )
#             instrument_stats = svc.compute_stats(
#                 current_price=prices[instrument.ticker]
#             )
#             stats[instrument.ticker] = instrument_stats
#         return stats