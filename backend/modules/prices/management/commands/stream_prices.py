import asyncio
import logging
from dataclasses import asdict

from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand
from polygon.websocket.models import WebSocketMessage

from config.clients import polygon_websocket_client
from modules.instruments.models import Instrument
from modules.prices.constants import PRICES_CHANNEL_LAYER

logger = logging.getLogger(__name__)


class PriceStream:
    def __init__(self):
        self.channel_layer = get_channel_layer()

    async def start(self, tickers: list[str]):
        await self.channel_layer.group_add(PRICES_CHANNEL_LAYER, "broadcast")
        tickers = ["A." + t for t in tickers]
        tickers_str = ",".join(tickers)
        polygon_websocket_client.subscribe(tickers_str)
        await polygon_websocket_client.connect(self._handle_msg)

    async def _handle_msg(self, msgs: list[WebSocketMessage]):
        data = [asdict(m) for m in msgs]
        data = {d["symbol"] for d in data}
        await self.channel_layer.group_send(
            PRICES_CHANNEL_LAYER, {"type": "broadcast.receive", "data": data}
        )


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Starting broadcasting real stocks...")
        sb = PriceStream()
        tickers = [i.ticker for i in Instrument.objects.all()]
        logger.info("Broadcasting %s stocks", len(tickers))
        asyncio.run(sb.start(tickers))
