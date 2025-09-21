from collections.abc import Iterator
from dataclasses import asdict
from datetime import datetime
from http.client import HTTPResponse
from typing import Any

from django.http.response import Http404
from django.shortcuts import get_object_or_404
from polygon import RESTClient as PolygonClient
from polygon.exceptions import BadResponse
from polygon.rest.models.snapshot import Agg

from config.clients import polygon_client
from config.settings import POLYGON_ASSET_TYPE
from modules.instruments.models import Instrument
from modules.prices.exceptions import PayloadTooLarge
from modules.prices.schemas import DailyPriceSummary, DailySummary


class PolygonPricesRepository:

    def __init__(self, client: PolygonClient = None):  # type: ignore
        self.polygon_client = client or polygon_client

    def get_ohlc(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        interval_multiplier: int,
    ) -> list[dict[str, Any]] | None:
        get_object_or_404(Instrument, ticker=ticker.upper())

        try:
            aggs = self.polygon_client.list_aggs(
                ticker=ticker.upper(),
                multiplier=interval_multiplier,
                timespan=interval.lower(),
                from_=start_date,
                to=end_date,
            )
        except BadResponse:
            return None

        return self._aggs_to_json(aggs, max_aggs=10_000)

    @classmethod
    def _aggs_to_json(cls, aggs: Iterator[Agg], max_aggs: int) -> list[dict[str, Any]]:
        bars = []
        for a in aggs:
            bars.append(cls._agg_to_json(a))
            if len(bars) > max_aggs:
                raise PayloadTooLarge()
        return bars

    @staticmethod
    def _agg_to_json(agg: Agg) -> dict[str, Any]:
        data = asdict(agg)
        data["timestamp"] = datetime.fromtimestamp(data["timestamp"] / 1000)
        return data

    def get_price(self, ticker: str) -> DailyPriceSummary | None:
        ticker_upper = ticker.upper()
        get_object_or_404(Instrument, ticker=ticker_upper)

        try:
            snapshot = self.polygon_client.get_snapshot_ticker(
                market_type=POLYGON_ASSET_TYPE, ticker=ticker_upper
            )
        except BadResponse:
            return None

        if isinstance(snapshot, HTTPResponse):
            return None

        required_fields = [
            "min",
            "day",
            "todays_change",
            "todays_change_percent",
            "updated",
        ]

        for field in required_fields:
            if not getattr(snapshot, field, None):
                return None

        return DailyPriceSummary.from_snapshot(snapshot)

    def get_prices(
        self, tickers: list[str], include_otc: bool = False
    ):
        tickers = [t.upper() for t in tickers]
        if len(tickers) > 50:
            raise PayloadTooLarge("Maximum of 50 tickers allowed per request.")

        if Instrument.objects.filter(ticker__in=tickers).count() != len(tickers):
            raise Http404("One or more tickers not found in the database.")

        try:
            snapshots = self.polygon_client.get_snapshot_all(
                POLYGON_ASSET_TYPE,
                tickers=tickers,
                include_otc=include_otc,
            )
        except BadResponse:
            return None

        if isinstance(snapshots, HTTPResponse):
            return None

        return list(map(DailyPriceSummary.from_snapshot, snapshots))
