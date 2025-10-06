import asyncio
import logging
import os
import random
import socket
import time

from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand

from modules.instruments.models import Instrument
from modules.prices.constants import PRICES_CHANNEL_LAYER

logger = logging.getLogger(__name__)


class PriceStreamMock:
    async def start(self, tickers: list[str]):
        channel_layer = get_channel_layer()
        await channel_layer.group_add(PRICES_CHANNEL_LAYER, "broadcast")
        while True:
            data = {t: self.get_random_ohlc(t) for t in tickers}
            await channel_layer.group_send(
                PRICES_CHANNEL_LAYER, {"type": "broadcast.receive", "data": data}
            )

            await asyncio.sleep(1)

    def get_random_ohlc(self, ticker: str) -> dict:
        now_ms = int(time.time() * 1000)
        return {
            "symbol": ticker,
            "volume": random.randint(1000, 10000),
            "accumulated_volume": random.randint(1_000_000, 10_000_000),
            "official_open_price": round(op := random.uniform(0.4, 1.0), 4),
            "vwap": round(vw := (op + random.uniform(-0.01, 0.01)), 4),
            "open": round(o := (vw + random.uniform(-0.002, 0.002)), 4),
            "close": round(c := (vw + random.uniform(-0.002, 0.002)), 4),
            "high": round(max(o, c) + random.uniform(0, 0.002), 4),
            "low": round(min(o, c) - random.uniform(0, 0.002), 4),
            "aggregate_vwap": round(op + random.uniform(-0.02, 0.02), 4),
            "average_size": random.randint(100, 1000),
            "start_timestamp": now_ms - 1000,
            "end_timestamp": now_ms,
        }


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.error("Starting broadcasting fake stocks...")
        postgres_host = os.environ.get("POSTGRES_HOST", "postgresql-postgresql")
        logger.error("POSTGRES_HOST: %s", postgres_host)
        try:
            ip = socket.gethostbyname(postgres_host)
            logger.error("Resolved %s to %s", postgres_host, ip)
        except socket.gaierror as e:
            logger.error("Failed to resolve %s: %s", postgres_host, e)
        sb = PriceStreamMock()
        tickers = [i.ticker for i in Instrument.objects.all()]
        logger.info("Broadcasting %s stocks", len(tickers))
        asyncio.run(sb.start(tickers))
