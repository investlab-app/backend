import asyncio
import logging
from dataclasses import asdict

from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand
from polygon import WebSocketClient
from polygon.websocket.models import Feed, Market, WebSocketMessage

from config.settings import POLYGON_SECRET_KEY
from config.polygon import websocket_client
from modules.instruments.models import Instrument


class PriceStream:
    def __init__(self):
        self.channel_layer = get_channel_layer()

    async def start(self, tickers: list[str]):
        await self.channel_layer.group_add("tickers_broadcast", "broadcast")
        tickers = ["A." + t for t in tickers]
        tickers_str = ",".join(tickers)
        websocket_client.subscribe(tickers_str)
        await websocket_client.connect(self._handle_msg)

    async def _handle_msg(self, msgs: list[WebSocketMessage]):
        data = [asdict(m) for m in msgs]
        data = {d["symbol"] for d in data}
        await self.channel_layer.group_send(
            "tickers_broadcast", {"type": "broadcast.receive", "data": data}
        )


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.info("Starting broadcasting real stocks...")
        sb = PriceStream()
        tickers = [i.ticker for i in Instrument.objects.all()]  # ty: ignore
        logging.info(f"Broadcasting {len(tickers)} stocks")
        asyncio.run(sb.start(tickers))
