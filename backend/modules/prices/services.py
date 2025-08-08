
from dataclasses import asdict
from datetime import datetime

from django.shortcuts import get_object_or_404

from config.logging import get_logger
from config.polygon import client
from modules.instruments.models import Instrument
from modules.prices.exceptions import PayloadTooLarge

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
        aggs = client.list_aggs(
            ticker.lower(), interval_multiplier, interval.lower(), start_date, end_date
        )
        return PricesV2Service._aggs_to_json(aggs, max_aggs=10_000)


    @staticmethod
    def _aggs_to_json(aggs, max_aggs):
        bars = []
        for a in aggs:
            bars.append(PricesV2Service._agg_to_json(a))
            if len(bars) > max_aggs:
                raise PayloadTooLarge

    @staticmethod
    def _agg_to_json(agg):
        data = asdict(agg)
        data["timestamp"] = datetime.fromtimestamp(data["timestamp"] / 1000)
        return data
