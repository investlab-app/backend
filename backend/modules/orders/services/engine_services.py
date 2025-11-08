import asyncio
import uuid
from decimal import Decimal

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.db import transaction

from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.orders.models import Order
from modules.orders.order_engine.converters import (
    asset_to_engine_asset,
    order_to_engine_order,
)
from modules.orders.order_engine.engine import TradeEngine
from modules.orders.order_engine.structures import (
    EngineOrderUpdate,
    EngineTransaction,
    MarketEngineOrderUpdate,
    TradeEngineInput,
    TradeEngineOutput,
)
from modules.orders.services.order_services import MarketOrderService
from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.transactions.schemas import TransactionParams
from modules.transactions.services import ExecuteTransactionService


class RunOrderEngineService:
    def __init__(self):
        self.data_fetcher = TradeEngineDataFetcher()
        self.price_listener = PricesFetcher()
        self.output_handler = TradeEngineOutputHandler()
        self.engine = TradeEngine()

    async def run(self):
        asyncio.ensure_future(self.price_listener.run())
        while True:
            data = await self.data_fetcher.fetch()
            prices = self.price_listener.get_prices()
            data.prices = prices

            output = self.engine.run(prices)

            await self.output_handler.handle(output)


class TradeEngineDataFetcher:
    async def fetch(self) -> TradeEngineInput:
        (orders, assets, balances) = await database_sync_to_async(
            self._prefetch_data_sync
        )()
        return TradeEngineInput(
            orders=orders, assets=assets, prices={}, balances=balances
        )

    def _prefetch_data_sync(self):
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
    def __init__(self):
        self._prices = {}

    async def run(self):
        self.layer = get_channel_layer()
        await asyncio.ensure_future(self._update_input_prices(self.layer))

    async def _update_input_prices(self, layer):
        channel = await layer.new_channel()
        await layer.group_add(PRICES_CHANNEL_LAYER, channel)

        while True:
            ticker_data = await layer.receive(channel)
            for ticker, data in ticker_data["data"].items():
                self._prices[ticker] = (
                    Decimal(data["high"]) + Decimal(data["low"])
                ) / 2

    def get_prices(self):
        return self._prices


class TradeEngineOutputHandler:
    def __init__(self, order_service: MarketOrderService | None = None):
        self.order_service = order_service or MarketOrderService()

    async def handle(self, output: TradeEngineOutput, prices: dict[str, float]):
        await database_sync_to_async(self._handle_output_sync)(output, prices)

    def _handle_output_sync(self, output: TradeEngineOutput, prices: dict[str, float]):
        with transaction.atomic():
            self._handle_completed_orders(output.completed_orders)
            self._handle_updated_orders(output.updated_orders)
            self._handle_transactions(output.transactions, prices)

    def _handle_completed_orders(self, orders: list[uuid.UUID]):
        for order in Order.objects.filter(id__in=orders):
            self.order_service.delete(order)

    def _handle_updated_orders(self, orders: list[EngineOrderUpdate]):
        ids = [o.id for o in orders]
        orders_dict = {o.id: o for o in orders}
        real_orders = Order.objects.filter(id__in=ids).prefetch_related("detail")

        for o in real_orders:
            corresponding_engine_order = orders_dict[o.id]
            if isinstance(corresponding_engine_order, MarketEngineOrderUpdate):
                o.detail.volume_processed = corresponding_engine_order.volume_processed
                o.detail.save()
            else:
                raise ValueError("Object not supported")

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
