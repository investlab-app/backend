import asyncio
import logging
from dataclasses import asdict

from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand
from polygon.websocket.models import WebSocketMessage

from config.clients import polygon_websocket_client
from modules.instruments.models import Instrument
from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.prices.schemas import PriceBar
from modules.prices.services import LatestPriceService, PriceService

logger = logging.getLogger(__name__)


class PriceStream:
    def __init__(
        self,
        prices_service: PriceService | None = None,
        latest_price_service: LatestPriceService | None = None,
    ):
        self.channel_layer = get_channel_layer()

        self.price_service = prices_service or PriceService()
        self.latest_price_service = latest_price_service or LatestPriceService()

        initial_prices = prices_service.get_latest_daily_bars_from_last_n_days(7)
        self.latest_price_service.update_prices(initial_prices)

    async def start(self, tickers: list[str]):
        await self.channel_layer.group_add(PRICES_CHANNEL_LAYER, "broadcast")
        tickers = ["A." + t for t in tickers]
        tickers_str = ",".join(tickers)
        polygon_websocket_client.subscribe(tickers_str)
        await polygon_websocket_client.connect(self._handle_msg)

    async def _handle_msg(self, msgs: list[WebSocketMessage]):
        data = [asdict(m) for m in msgs]

        price_bars = {d["symbol"]: PriceBar.from_ws(d) for d in data}
        prices = {d["symbol"]: d for d in data}

        self.latest_price_service.update_prices(price_bars)
        await self.channel_layer.group_send(
            PRICES_CHANNEL_LAYER, {"type": "broadcast.receive", "data": prices}
        )


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Starting broadcasting real stocks...")
        sb = PriceStream()
        tickers = [i.ticker for i in Instrument.objects.all()]
        logger.info("Broadcasting %s stocks", len(tickers))
        asyncio.run(sb.start(tickers))
