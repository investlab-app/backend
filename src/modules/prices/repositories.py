from datetime import datetime, timedelta
from decimal import Decimal
from http.client import HTTPResponse
from zoneinfo import ZoneInfo

from django.http.response import Http404
from django.shortcuts import get_object_or_404
from polygon import RESTClient as PolygonClient
from polygon.exceptions import BadResponse

from config.clients import polygon_client
from config.settings import POLYGON_ASSET_TYPE
from modules.core.exceptions import PayloadTooLargeException
from modules.instruments.models import Instrument
from modules.prices.schemas import PriceBar, PriceDailySummary


class PolygonPricesRepository:
    def __init__(self, client: PolygonClient | None = None):
        self.polygon_client = client or polygon_client

    def get_ohlc(
        self,
        ticker: str,
        start_date: datetime | int,
        end_date: datetime | int,
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
                limit=50000,
            )
        except BadResponse:
            return None

        if isinstance(aggs, HTTPResponse):
            return None

        results = []
        for idx, agg in enumerate(aggs, start=1):
            if idx > 10_000:
                raise PayloadTooLargeException
            results.append(PriceBar.from_agg(agg))
        print(len(results))

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
            raise PayloadTooLargeException(
                "Maximum of 200 tickers allowed per request."
            )

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

    def get_prices_at(
        self, instruments: list[Instrument], timestamp: datetime
    ) -> dict[Instrument, Decimal]:
        prices = {}
        for instrument in instruments:
            ohlc = self.get_ohlc(
                ticker=instrument.ticker,
                start_date=timestamp,
                end_date=timestamp + timedelta(minutes=10),
                interval="minute",
                interval_multiplier=1,
            )
            if ohlc and len(ohlc) > 0:
                prices[instrument] = ohlc[0].open
        return prices

    def get_price_at(self, ticker: str, timestamp: datetime) -> Decimal | None:
        ohlc = self.get_ohlc(
            ticker=ticker,
            start_date=timestamp,
            end_date=timestamp + timedelta(minutes=10),
            interval="minute",
            interval_multiplier=1,
        )
        if ohlc and len(ohlc) > 0:
            return ohlc[0].open
        return None

    def get_prices_map(self, tickers: list[str]) -> dict[str, PriceDailySummary] | None:
        prices = self.get_prices(tickers)
        if prices is None:
            return None

        return {price.ticker: price for price in prices}

    def get_daily_market_summary(
        self, timestamp: datetime
    ) -> dict[str, PriceBar] | None:
        timestamp = timestamp.astimezone(ZoneInfo("America/New_York"))

        try:
            aggs = self.polygon_client.get_grouped_daily_aggs(
                timestamp.strftime("%Y-%m-%d")
            )
            bars = {agg.ticker: PriceBar.from_agg(agg) for agg in aggs}
            return bars
        except Exception:
            return None
