import asyncio
import copy

from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.db import transaction

from modules.investors.models import Asset, Investor
from modules.orders.models import Order
from modules.orders.order_engine.converters import (
    asset_to_engine_asset,
    order_to_engine_order,
)
from modules.orders.order_engine.engine import TradeEngine
from modules.orders.order_engine.structures import (
    EngineOrder,
    EngineTransaction,
    MarketEngineOrder,
    TradeEngineInput,
    TradeEngineOutput,
)
from modules.prices.constants import PRICES_CHANNEL_LAYER


class RunOrderEngineService:
    async def run(self):
        self.layer = get_channel_layer()
        self.prices = {}

        asyncio.ensure_future(self._update_input_prices(self.layer))
        await self._run_engine()

    async def _update_input_prices(self, layer):
        channel = await layer.new_channel()
        await layer.group_add(PRICES_CHANNEL_LAYER, channel)

        while True:
            prices = {}
            ticker_data = await layer.receive(channel)
            for ticker, data in ticker_data["data"].items():
                prices[ticker] = (data["high"] + data["low"]) / 2

            self.prices = prices

    async def _run_engine(self):
        engine_input = TradeEngineAsyncInput()
        engine_output = TradeEngineAsyncOutput()

        engine = TradeEngine(engine_input, engine_output)

        while True:
            await engine_input.prefetch_data()
            engine_input.prices = copy.deepcopy(self.prices)
            engine.run()
            await engine_output.handle_output()

            await asyncio.sleep(1)


class TradeEngineAsyncInput:
    def __init__(self):
        self.prices = {}

    def _prefetch_data_sync(self):
        with transaction.atomic():
            assets = list(Asset.objects.all())
            orders = list(Order.objects.prefetch_related("detail"))
            investors = list(Investor.objects.all())

            engine_orders = [order_to_engine_order(o) for o in orders]
            engine_assets = [asset_to_engine_asset(a) for a in assets]
            balances = {i.id: i.balance for i in investors}

            return engine_orders, engine_assets, balances

    async def prefetch_data(self):
        (
            self.engine_orders,
            self.engine_assets,
            self.balances,
        ) = await database_sync_to_async(self._prefetch_data_sync)()

    def __call__(self) -> TradeEngineInput:
        i = TradeEngineInput(
            orders=self.engine_orders,
            assets=self.engine_assets,
            prices=self.prices,
            balances=self.balances,
        )
        return i


class TradeEngineAsyncOutput:
    def __call__(self, output: TradeEngineOutput, prices: dict[str, float]):
        self.output = output
        self.prices = prices

    async def handle_output(self):
        await database_sync_to_async(self._handle_output_sync)(self.output, self.prices)

    def _handle_output_sync(self, output: TradeEngineOutput, prices: dict[str, float]):
        with transaction.atomic():
            self._handle_completed_orders(output.completed_orders)
            self._handle_updated_orders(output.updated_orders)
            self._handle_transactions(output.transactions, prices)

    def _handle_completed_orders(self, orders: list[EngineOrder]):
        ids = [o.id for o in orders]
        Order.objects.filter(id__in=ids).delete()

    def _handle_updated_orders(self, orders: list[EngineOrder]):
        ids = [o.id for o in orders]
        orders = {o.id: o for o in orders}
        real_orders = Order.objects.filter(id__in=ids).prefetch_related("details")

        for o in real_orders:
            corresponding_engine_order = orders[o.id]
            if isinstance(corresponding_engine_order, MarketEngineOrder):
                o.detail.volume_processed = corresponding_engine_order.volume_processed
                o.detail.save()
            else:
                raise ValueError("Object not supported")

    def _handle_transactions(
        self, transactions: list[EngineTransaction], prices: dict[str, float]
    ):
        investor_ids = [t.investor_id for t in transactions]
        investors = Investor.objects.filter(id__in=investor_ids)
        investors = {i.id: i for i in investors}

        for t in transactions:
            if t.is_buy:
                # TODO: there should be an actual call to buy/sell
                print("Bought some shit")
                print(f"Ticker: {t.ticker}")
                print(f"Volume: {t.volume}")
                print(f"Price: {prices[t.ticker]}")
                print("\n\n\n")
                # buy(investor, t.ticker, t.volume, prices[t.ticker])
            else:
                # TODO: there should be an actual call to buy/sell
                print("Sold some shit")
                print(f"Ticker: {t.ticker}")
                print(f"Volume: {t.volume}")
                print(f"Price: {prices[t.ticker]}")
                print("\n\n\n")
                # sell(investor, t.ticker, t.volume, prices[t.ticker])
