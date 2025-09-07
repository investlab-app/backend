from dataclasses import asdict
from datetime import datetime
from http.client import HTTPResponse

from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404

from config.clients import polygon_client
from config.logging import get_logger
from config.settings import POLYGON_ASSET_TYPE
from modules.instruments.models import Instrument
from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.prices.exceptions import PayloadTooLarge
from modules.prices.models import LatestPrice

logger = get_logger(__name__)


class PricesV2Service:
    @staticmethod
    def get_ohlc(
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        interval_multiplier: int,
    ):
        get_object_or_404(Instrument, ticker=ticker.upper())
        aggs = polygon_client.list_aggs(
            ticker.upper(), interval_multiplier, interval.lower(), start_date, end_date
        )
        return PricesV2Service._aggs_to_json(aggs, max_aggs=10_000)

    @staticmethod
    def _aggs_to_json(aggs, max_aggs):
        bars = []
        for a in aggs:
            bars.append(PricesV2Service._agg_to_json(a))
            if len(bars) > max_aggs:
                raise PayloadTooLarge
        return bars

    @staticmethod
    def _agg_to_json(agg):
        data = asdict(agg)
        data["timestamp"] = datetime.fromtimestamp(data["timestamp"] / 1000)
        return data

    @staticmethod
    def get_price_info(ticker: str):
        ticker_upper = ticker.upper()
        get_object_or_404(Instrument, ticker=ticker_upper)

        ticker_snapshot = polygon_client.get_snapshot_ticker(
            market_type=POLYGON_ASSET_TYPE, ticker=ticker_upper
        )

        if isinstance(ticker_snapshot, HTTPResponse):
            raise ValueError(
                f"HTTP error {ticker_snapshot.status}: "
                f"{ticker_snapshot.reason} - {ticker_snapshot.msg}"
            )

        if not ticker_snapshot.min:
            raise ValueError(f"No minute data found for ticker {ticker_upper}")

        if not ticker_snapshot.day:
            raise ValueError(f"No daily summary found for ticker {ticker_upper}")

        if not ticker_snapshot.todays_change:
            raise ValueError(f"No today's change found for ticker {ticker_upper}")

        if not ticker_snapshot.todays_change_percent:
            raise ValueError(
                f"No today's change percentage found for ticker {ticker_upper}"
            )

        if not ticker_snapshot.updated:
            raise ValueError(
                f"No last updated timestamp found for ticker {ticker_upper}"
            )

        return {
            "current_price": ticker_snapshot.min.close,
            "daily_summary": {
                "open": ticker_snapshot.day.open,
                "high": ticker_snapshot.day.high,
                "low": ticker_snapshot.day.low,
                "close": ticker_snapshot.day.close,
                "volume": ticker_snapshot.day.volume,
                "volume_weighted_average_price": ticker_snapshot.day.vwap,
            },
            "todays_change": ticker_snapshot.todays_change,
            "todays_change_percent": ticker_snapshot.todays_change_percent,
            "last_updated": ticker_snapshot.updated,
        }

class LatestPriceSaveService:
    def __init__(self):
        self.channel_layer = get_channel_layer()

    async def run(self):
        channel_name = await self.channel_layer.new_channel()
        await self.channel_layer.group_add(PRICES_CHANNEL_LAYER, channel_name)
        logger.info("Listening for prices...")

        while True:
            message = await self.channel_layer.receive(channel_name)
            if message["type"] == "broadcast.receive":
                await self.save_prices(message["data"])

    @staticmethod
    async def save_prices(data):
        for ticker, values in data.items():
            price = (values["low"] + values["high"]) / 2
            await LatestPrice.objects.aupdate_or_create(
                ticker=ticker, defaults={"price": price}
            )