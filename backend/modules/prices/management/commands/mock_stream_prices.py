import asyncio
import random
import time
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from modules.instruments.models import Instrument

class PriceStreamMock:
    async def start(self, tickers :list[str]):
        channel_layer = get_channel_layer()
        await channel_layer.group_add('tickers_broadcast', 'broadcast')
        while True:
            data = {t: self.get_random_ohlc(t) for t in tickers}
            await channel_layer.group_send(
                'tickers_broadcast',
                {'type': 'broadcast.receive', 'data': data}
            )
            
            await asyncio.sleep(1)


    def get_random_ohlc(self, ticker: str) -> dict:
        now_ms = int(time.time() * 1000)
        return {
            "sym": ticker,
            "v": random.randint(1000, 10000),
            "av": random.randint(1_000_000, 10_000_000),
            "op": round(op := random.uniform(0.4, 1.0), 4),
            "vw": round(vw := (op + random.uniform(-0.01, 0.01)), 4),
            "o": round(o := (vw + random.uniform(-0.002, 0.002)), 4),
            "c": round(c := (vw + random.uniform(-0.002, 0.002)), 4),
            "h": round(max(o, c) + random.uniform(0, 0.002), 4),
            "l": round(min(o, c) - random.uniform(0, 0.002), 4),
            "a": round(op + random.uniform(-0.02, 0.02), 4),
            "z": random.randint(100, 1000),
            "s": now_ms - 1000,
            "e": now_ms
        }

class Command(BaseCommand):
    def handle(self, *args, **options):
        print(f'Starting broadcasting fake stocks...')
        sb = PriceStreamMock()
        tickers = [i.ticker for i in Instrument.objects.all()]
        print(f'Broadcasting {len(tickers)} stocks')
        asyncio.run(sb.start(tickers))