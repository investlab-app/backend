import uuid
from collections import defaultdict
from decimal import Decimal
from time import sleep

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.markets.repositories import PolygonMarketsRepository
from modules.orders.models import Order
from modules.orders.order_engine.converters import (
    asset_to_engine_asset,
    order_to_engine_order,
)
from modules.orders.order_engine.engine import TradeEngine
from modules.orders.order_engine.structures import (
    EngineOrderUpdate,
    EngineTransaction,
    TradeEngineInput,
    TradeEngineOutput,
)
from modules.orders.services.order_services import OrderService
from modules.prices.services import LatestPriceService
from modules.transactions.schemas import TransactionParams
from modules.transactions.services import ExecuteTransactionService


class RunOrderEngineService:
    def __init__(self):
        self.data_fetcher = TradeEngineDataFetcher()
        self.price_listener = PricesFetcher()
        self.output_handler = TradeEngineOutputHandler()
        self.engine = TradeEngine()
        self.markets_repository = PolygonMarketsRepository()

    def run(self):
        while True:
            if self.markets_repository.is_nasdaq_open():
                data = self.data_fetcher.fetch()
                prices = self.price_listener.get_prices()
                data.prices = prices
                output = self.engine.run(data)
                self.output_handler.handle(output, prices)
            else:
                sleep(60)


class TradeEngineDataFetcher:
    def fetch(self) -> TradeEngineInput:
        (orders, assets, balances) = self._fetch_data()
        return TradeEngineInput(
            orders=orders,
            assets=assets,
            prices={},
            balances=balances,
        )

    def _fetch_data(self):
        with transaction.atomic():
            assets: list[Asset] = list(Asset.objects.all())  # ty: ignore
            orders: list[Order] = list(  # ty: ignore[invalid-assignment]
                Order.objects.prefetch_related("detail")
            )
            investors: list[Investor] = list(Investor.objects.all())  # ty: ignore

            engine_orders = [order_to_engine_order(o) for o in orders]
            engine_assets = [asset_to_engine_asset(a) for a in assets]
            balances = {str(i.id): i.balance for i in investors}

            return engine_orders, engine_assets, balances


class PricesFetcher:
    def __init__(self, latest_price_service: LatestPriceService | None = None):
        self.latest_price_service = latest_price_service or LatestPriceService()

    def get_prices(self):
        return self.latest_price_service.get_prices()


class TradeEngineOutputHandler:
    def __init__(self, order_service: OrderService | None = None):
        self.order_service = order_service or OrderService()

    def handle(self, output: TradeEngineOutput, prices: dict[str, float]):
        with transaction.atomic():
            updates = self._collect_affected_data(output)

            self._handle_completed_orders(output.completed_orders)
            self._handle_updated_orders(output.updated_orders)
            self._handle_transactions(output.transactions, prices)

            if updates:
                self._send_order_update(updates)

    def _collect_affected_data(self, output: TradeEngineOutput) -> dict[str, set[str]]:
        updates = defaultdict(set)

        if output.completed_orders:
            completed_orders_qs = (
                Order.objects.filter(id__in=output.completed_orders)
                .select_related("ticker")
                .only("investor_id", "ticker__ticker")
            )
            for o in completed_orders_qs:
                updates[str(o.investor_id)].add(o.ticker.ticker)

        if output.updated_orders:
            updated_ids = [o.id for o in output.updated_orders]
            updated_orders_qs = (
                Order.objects.filter(id__in=updated_ids)
                .select_related("ticker")
                .only("investor_id", "ticker__ticker")
            )
            for o in updated_orders_qs:
                updates[str(o.investor_id)].add(o.ticker.ticker)

        for t in output.transactions:
            updates[str(t.investor_id)].add(t.ticker)

        return updates

    def _handle_completed_orders(self, orders: list[uuid.UUID]):
        for order in Order.objects.filter(id__in=orders).prefetch_related("detail"):
            self.order_service.delete(order)

    def _handle_updated_orders(self, orders: list[EngineOrderUpdate]):
        ids = [o.id for o in orders]
        orders_dict = {o.id: o for o in orders}
        real_orders = Order.objects.filter(id__in=ids).prefetch_related("detail")

        for o in real_orders:
            corresponding_engine_order = orders_dict[o.id]
            o.detail.volume_processed = corresponding_engine_order.volume_processed
            o.detail.save()

    def _handle_transactions(
        self, transactions: list[EngineTransaction], prices: dict[str, Decimal]
    ):
        investor_ids = [t.investor_id for t in transactions]
        investors = Investor.objects.filter(id__in=investor_ids)  # ty: ignore[invalid-assignment]
        investors = {str(i.pk): i for i in investors}

        ticker_names = [t.ticker for t in transactions]
        ticker_list = Instrument.objects.filter(ticker__in=ticker_names)
        tickers = {i.ticker: i for i in ticker_list}
        transaction_service = ExecuteTransactionService()

        for t in transactions:
            transaction_params = TransactionParams(
                investor=investors[t.investor_id],
                ticker=tickers[t.ticker],
                volume=t.volume,
                action_price=prices[t.ticker],
            )
            if t.is_buy:
                transaction_service.buy(transaction_params)
            else:
                transaction_service.sell(transaction_params)

    def _send_order_update(
        self,
        updates: dict[str, set[str]],
    ):
        channel_layer = get_channel_layer()
        for investor_id, tickers in updates.items():
            async_to_sync(channel_layer.group_send)(
                f"investor_{investor_id}",
                {
                    "type": "send_order_update",
                    "data": {"tickers": list(tickers)},
                },
            )
