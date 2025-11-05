from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
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


class PriceProvider:
    data: dict[str, list[PricePoint]]
    data_to_prefetch: dict[str, PrefetchRange]

    def __init__(
        self,
        fetcher: "PriceFetcher",
        prefetch_strategy: "PrefetchStrategy",
        select_strategy: "PriceSelectStrategy",
    ):
        self.fetcher = fetcher
        self.prefetch_strategy = prefetch_strategy
        self.price_select_strategy = select_strategy
        self.data = None
        self.data_to_prefetch = {}

    def prefetch_data(self):
        self.data = self.fetcher.fetch(self.price_ranges)

    def lazy_prefetch_single_ticker(self, ticker: str, data_range: PrefetchRange):
        if ticker in self.data_to_prefetch:
            current_range = self.data_to_prefetch[ticker]
            current_range.min_time = min(current_range.min_time, data_range.min_time)
            current_range.max_time = max(current_range.max_time, data_range.max_time)
        else:
            self.data_to_prefetch[ticker] = data_range

    def get_price(self, ticker: str, date_at: datetime):
        if self.data is None:
            raise ValueError("Prefetch was never called")
        if ticker not in self.data:
            raise ValueError(f"{ticker} was never prefetched")
        return self.prefetch_strategy.select(self.data[ticker], date_at)

    def clear(self):
        raise NotImplementedError()


class PrefetchStrategy:
    def __init__(self, samples=100):
        self.samples = samples

    def calculate(
        self, prices_to_prefetch: list[(str, datetime, datetime)]
    ) -> list[FetcherData]:
        fetcher_data = []
        for ticker, max_time, min_time in prices_to_prefetch:
            total_seconds = int((max_time - min_time).total_seconds())
            if self.samples > 1:
                interval_seconds = max(1, total_seconds // (self.samples))
            else:
                interval_seconds = total_seconds

            value, unit = self._best_interval_unit(interval_seconds)

            fetcher_data.append(
                FetcherData(
                    ticker=ticker,
                    min_time=min_time,
                    max_time=max_time,
                    interval=unit,
                    interval_multiplier=int(value),
                )
            )
        return fetcher_data

    def _best_interval_unit(self, seconds):
        if seconds < 60:
            return seconds, "s"
        if seconds < 60 * 60:
            return seconds / 60, "m"
        if seconds < 60 * 60 * 24:
            return seconds / (60 * 60), "h"
        else:
            return seconds / (60 * 60 * 24), "d"


class PriceSelectStrategy:
    def select(self, prices: list[PricePoint], time_at: datetime):
        return min(
            prices, key=lambda p: abs((p.date_at - time_at).total_seconds())
        ).price


class PriceFetcher:
    def __init__(self, price_repository, samples=100):
        self.price_repository = price_repository
        self.samples = samples

    def fetch(self, fetcher_data: list[FetcherData]) -> dict[str, list[PricePoint]]:
        result = defaultdict(list)
        for fd in fetcher_data:
            bars = self.price_repository.get_ohlc(
                fd.ticker,
                fd.max_time,
                fd.min_time,
                interval=fd.interval,
                interval_multiplier=fd.interval_multiplier,
            )
            for bar in bars:
                price = PricePoint(bar.close, bar.timestamp)
                result[fd.ticker].append(price)
        return result
