from collections import defaultdict
from decimal import Decimal
from typing import Any

from modules.core.defaults import PrecisionType
from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineOrder,
    EngineTransaction,
    MarketEngineOrder,
    MarketEngineOrderUpdate,
    TradeEngineInput,
    TradeEngineOutput,
)


class TradeEngine:
    def run(
        self,
        engine_input: TradeEngineInput,
    ):
        orders = engine_input.orders
        prices = engine_input.prices
        assets = engine_input.assets

        orders_by_investor = self._group_orders_by_investor(orders)
        assets_by_investor = self._group_assets_by_investor(assets)
        updated_orders = []
        completed_orders = []
        transactions = []

        engine = SingleInvestorTradeEngine()
        for investor_id in orders_by_investor:
            (
                investor_transactions,
                investor_modified_orders,
                investor_completed_orders,
            ) = engine.process_orders(
                orders_by_investor[investor_id],
                assets_by_investor[investor_id],
                prices,
                engine_input.balances[investor_id],
            )
            self._assign_investor(investor_transactions, investor_id)
            transactions.extend(investor_transactions)
            updated_orders.extend(investor_modified_orders)
            completed_orders.extend(investor_completed_orders)

        return TradeEngineOutput(
            transactions=transactions,
            updated_orders=updated_orders,
            completed_orders=completed_orders,
        )

    def _group_orders_by_investor(
        self, orders: list[EngineOrder]
    ) -> dict[Any, list[EngineOrder]]:
        result = defaultdict(list)
        [result[o.investor_id].append(o) for o in orders]
        return dict(result)

    def _group_assets_by_investor(
        self, assets: list[EngineAsset]
    ) -> dict[Any, dict[str, Decimal]]:
        result = defaultdict(dict)
        for asset in assets:
            result[asset.investor_id][asset.ticker] = asset.volume
        return result

    def _assign_investor(self, transactions: list[EngineTransaction], investor_id: int):
        for t in transactions:
            t.investor_id = investor_id


class SingleInvestorTradeEngine:
    def process_orders(
        self,
        orders: list[EngineOrder],
        assets: list[EngineAsset],
        prices: dict[str, Decimal],
        balance: Decimal,
    ):
        self._orders = orders
        self._assets = assets
        self._prices = prices
        self._balance = balance

        self._transactions = []
        self._modified_orders = []
        self._completed_orders = []

        self._process_order_group()

        return self._transactions, self._modified_orders, self._completed_orders

    def _process_order_group(self):
        for o in self._orders:
            if o.ticker not in self._prices:
                continue
            if isinstance(o, MarketEngineOrder):
                self._handle_market_order(o)
            else:
                raise RuntimeError("Unsupported order type")

    def _handle_market_order(self, order: MarketEngineOrder):
        if order.is_buy:
            self._handle_market_buy(order)
        else:
            self._handle_market_sell(order)

    def _handle_market_buy(self, order: MarketEngineOrder):
        balance = self._balance
        ticker = order.ticker
        price = self._prices[ticker]

        volume_needed = order.volume - order.volume_processed
        volume = min(volume_needed, balance / price)
        if volume == 0:
            return

        self._transactions.append(
            EngineTransaction(ticker=ticker, volume=volume, is_buy=True)
        )
        self._balance -= volume * price
        order.volume_processed += volume
        if abs(order.volume - order.volume_processed) < PrecisionType.volume.precision:
            self._completed_orders.append(order.id)
        else:
            self._modified_orders.append(
                MarketEngineOrderUpdate(
                    id=order.id, volume_processed=order.volume_processed
                )
            )

    def _handle_market_sell(self, order: MarketEngineOrder):
        ticker = order.ticker
        price = self._prices[ticker]

        if ticker not in self._assets:
            return
        volume_needed = order.volume - order.volume_processed
        volume = min(volume_needed, self._assets[ticker])
        if volume == 0:
            return

        self._transactions.append(
            EngineTransaction(
                ticker=ticker,
                volume=volume,
                is_buy=False,
            )
        )
        self._balance += volume * price
        order.volume_processed += volume
        self._assets[ticker] -= volume
        if abs(order.volume - order.volume_processed) < PrecisionType.volume.precision:
            self._completed_orders.append(order.id)
        else:
            self._modified_orders.append(
                MarketEngineOrderUpdate(
                    id=order.id, volume_processed=order.volume_processed
                )
            )
