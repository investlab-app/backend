from modules.prices.schemas import PriceBar
from math import ceil, floor
from modules.prices.repositories import PolygonPricesRepository
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal


@dataclass
class FetcherData:
    ticker: str
    min_time: datetime
    max_time: datetime
    interval: str
    interval_multiplier: int


@dataclass
class PrefetchRange:
    min_time: datetime
    max_time: datetime


@dataclass
class PricePoint:
    price: Decimal
    date_at: datetime


# TODO 
# There's a problem with prefetching data for different date_at than now
# There is no good way to get the price of an instrument given a datetime
# OHLC bar can return empty list and ticker snapshot only works for 'now'
# Possible solution would be to try bigger and bigger OHLC bars, until one
# of them returns non-empty list. For now it won't work well when date_at != now()
class PriceProvider:
    fetched_ranges: dict[str, (datetime, datetime)]
    prices: dict[str, list[Decimal, datetime]]

    def __init__(
        self,
        repository :PolygonPricesRepository = None,
        samples=100,
    ):
        self.fetched_ranges = {}
        self.prices = {}
        self.repository = repository or PolygonPricesRepository()
        self.samples = samples

    def prefetch_data(self, data: dict[str, timedelta], date_at: datetime):
        for ticker, timespan in data.items():
            bars = self.repository.get_ohlc(
                ticker,
                date_at - timespan - timedelta(minutes=15),
                date_at - timedelta(minutes=15),
                'second',
                max(floor(timespan.total_seconds()  / self.samples), 1) # TODO add test for max
            )
            data = []
            for bar in bars:
                data.append((bar.close, bar.timestamp))
            if not data:
                snapshot = self.repository.get_price(ticker)
                data.append((snapshot.current_price, date_at))

            self.prices[ticker] = data
            self.fetched_ranges[ticker] = (date_at - timespan, date_at)

    def get_price(self, ticker: str, date_at: datetime):
        if not ticker in self.fetched_ranges:
            raise ValueError(f"Prefetch was not called for {ticker}")

        date_range = self.fetched_ranges[ticker]
        if date_at < date_range[0] or date_at > date_range[1]:
            raise ValueError(
                f"Price of {ticker} accessed outside of prefetched timerange"
            )

        return self._select_closest_price(ticker, date_at)

    def _select_closest_price(self, ticker: str, date_at: datetime):
        prices = self.prices[ticker]

        closest_price = None
        smallest_seconds_diff = None
        for price, timestamp in prices:
            seconds_diff = abs((date_at - timestamp).total_seconds())
            if smallest_seconds_diff is None or seconds_diff < smallest_seconds_diff:
                closest_price = price
                smallest_seconds_diff = seconds_diff

        return closest_price


class MockPriceProvider:
    def __init__(self):
        self.prices = {}

    def prefetch_data(self, data: dict[str, timedelta], date_at: datetime):
        pass

    def set_prices(self, ticker: str, price_points: list[tuple[datetime, Decimal]]):
        self.prices[ticker] = sorted(price_points, key=lambda x: x[0])

    def get_price(self, ticker: str, date_at: datetime) -> Decimal | None:
        if ticker not in self.prices:
            return None
        points = self.prices[ticker]
        before = [p for d, p in points if d <= date_at]
        if not before:
            raise ValueError(f"You did not specify price for this date {date_at}")
        return before[-1]