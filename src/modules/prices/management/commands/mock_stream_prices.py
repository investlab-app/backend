import asyncio
import logging
import random
import time
from decimal import Decimal

from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand

from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.prices.schemas import PriceBar
from modules.prices.services import LatestPriceService, PriceService

logger = logging.getLogger(__name__)


class PriceStreamMock:
    initial_prices: dict[str, PriceBar]

    def __init__(
        self,
        price_service: PriceService | None = None,
        latest_price_service: LatestPriceService | None = None,
    ):
        price_service = price_service or PriceService()
        self.initial_prices = price_service.get_latest_daily_bars_from_last_n_days(7)
        self.latest_price_service = latest_price_service or LatestPriceService()

    def _randomize_value(self, value: Decimal | None):
        float_value = float(value or 0)
        val_range = min(float_value * 0.01, 0.25)
        return max(float_value + random.uniform(-val_range, val_range), 1)

    def _generate_prices(self):
        new_data = {}
        now_ms = int(time.time() * 1000)
        for ticker, price_bar in self.initial_prices.items():
            new_data[ticker] = {
                "symbol": ticker,
                "volume": self._randomize_value(price_bar.volume),
                "accumulated_volume": random.randint(1_000_000, 10_000_000),
                "official_open_price": self._randomize_value(price_bar.open),
                "vwap": self._randomize_value(price_bar.volume_weighted_average_price),
                "open": self._randomize_value(price_bar.open),
                "high": self._randomize_value(price_bar.high),
                "low": self._randomize_value(price_bar.low),
                "close": self._randomize_value(price_bar.close),
                "aggregate_vwap": self._randomize_value(
                    price_bar.volume_weighted_average_price
                ),
                "average_size": random.randint(100, 1000),
                "start_timestamp": now_ms - 1000,
                "end_timestamp": now_ms,
            }
        return new_data

    async def start(self):
        channel_layer = get_channel_layer()
        await channel_layer.group_add(PRICES_CHANNEL_LAYER, "broadcast")
        while True:
            data = self._generate_prices()
            price_bars = {
                ticker: PriceBar.from_ws(ohlc) for ticker, ohlc in data.items()
            }

            self.latest_price_service.update_prices(price_bars)
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
        logger.info("Starting broadcasting fake stocks...")
        sb = PriceStreamMock()
        asyncio.run(sb.start())
