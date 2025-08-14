import asyncio
import random
import time
from dataclasses import asdict
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from modules.instruments.models import Instrument
from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage, Feed, Market
from typing import List
from config.settings import POLYGON_SECRET_KEY

class PriceStream:
    def __init__(self):
        self.client = WebSocketClient(
            api_key=POLYGON_SECRET_KEY,
            feed=Feed.Delayed,
            market=Market.Stocks
        )
        self.channel_layer = get_channel_layer()

    async def start(self, tickers :list[str]):
        await self.channel_layer.group_add('tickers_broadcast', 'broadcast')
        tickers = ["A." + t for t in tickers]
        tickers = ','.join(tickers)
        self.client.subscribe(tickers)
        await self.client.connect(self._handle_msg)

    async def _handle_msg(self, msgs: List[WebSocketMessage]):
        data = [asdict(m) for m in msgs]
        data = {d['symbol'] for d in data}
        await self.channel_layer.group_send(
            'tickers_broadcast',
            {'type': 'broadcast.receive', 'data': data}
        )


class Command(BaseCommand):
    def handle(self, *args, **options):
        print(f'Starting broadcasting real stocks...')
        sb = PriceStream()
        tickers = [i.ticker for i in Instrument.objects.all()]
        print(f'Broadcasting {len(tickers)} stocks')
        asyncio.run(sb.start(tickers))