from datetime import datetime
from decimal import Decimal
from http.client import HTTPResponse

from django.http.response import Http404
from django.shortcuts import get_object_or_404
from polygon import RESTClient as PolygonClient
from polygon.exceptions import BadResponse

from config.clients import polygon_client
from config.settings import POLYGON_ASSET_TYPE
from modules.instruments.models import Instrument
from modules.prices.exceptions import PayloadTooLarge
from modules.prices.schemas import PriceBar, PriceDailySummary


class PolygonPricesRepository:
    def __init__(self, client: PolygonClient | None = None):
        self.polygon_client = client or polygon_client

    def get_ohlc(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
        interval_multiplier: int,
    ) -> list[PriceBar] | None:
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

        if isinstance(aggs, HTTPResponse):
            return None

        results = []
        for idx, agg in enumerate(aggs, start=1):
            if idx > 10_000:
                raise PayloadTooLarge
            results.append(PriceBar.from_agg(agg))

        return results

    def get_price(self, ticker: str) -> PriceDailySummary | None:
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

        return PriceDailySummary.from_snapshot(snapshot)

    def get_prices(self, tickers: list[str]) -> list[PriceDailySummary] | None:
        tickers = [t.upper() for t in tickers]
        if len(tickers) > 200:
            raise PayloadTooLarge("Maximum of 200 tickers allowed per request.")

        if Instrument.objects.filter(ticker__in=tickers).count() != len(tickers):
            raise Http404("One or more tickers not found in the database.")

        try:
            snapshots = self.polygon_client.get_snapshot_all(
                market_type=POLYGON_ASSET_TYPE,
                tickers=tickers,
                include_otc=False,
            )
        except BadResponse:
            return None

        if isinstance(snapshots, HTTPResponse):
            return None

        return list(map(PriceDailySummary.from_snapshot, snapshots))

    def get_prices_average_hl(self, tickers: list[Instrument]) -> dict[str, Decimal]:
        raise NotImplementedError()

    def get_prices_map(self, tickers: list[str]) -> dict[str, PriceDailySummary] | None:
        prices = self.get_prices(tickers)
        if prices is None:
            return None

        return {price.ticker: price for price in prices}
