from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from faker import Faker

from modules.graph_lang.framework.price_provider import (
    FetcherData,
    PrefetchRange,
    PrefetchStrategy,
    PriceFetcher,
    PricePoint,
    PriceProvider,
    PriceSelectStrategy,
)

fake = Faker()


class DummyFetcher:
    def fetch(self, fetcher_data):
        # Return dummy data for each ticker
        result = {}
        for fd in fetcher_data:
            result[fd.ticker] = [
                PricePoint(price=Decimal("100.0"), date_at=fd.min_time),
                PricePoint(price=Decimal("110.0"), date_at=fd.max_time),
            ]
        return result


class DummyPrefetchStrategy:
    def select(self, prices, date_at):
        # Return the first price for simplicity
        return prices[0].price


class DummySelectStrategy:
    def select(self, prices, time_at):
        # Return the price closest to time_at
        return min(
            prices, key=lambda p: abs((p.date_at - time_at).total_seconds())
        ).price


class TestPriceProvider:
    def setup_method(self):
        self.fetcher = DummyFetcher()
        self.prefetch_strategy = DummyPrefetchStrategy()
        self.select_strategy = DummySelectStrategy()
        self.provider = PriceProvider(
            self.fetcher, self.prefetch_strategy, self.select_strategy
        )
        self.provider.price_ranges = [
            MagicMock(
                ticker="AAPL",
                min_time=datetime(2020, 1, 1),
                max_time=datetime(2020, 1, 2),
                interval="1d",
            ),
            MagicMock(
                ticker="GOOG",
                min_time=datetime(2020, 1, 1),
                max_time=datetime(2020, 1, 2),
                interval="1d",
            ),
        ]

    def test_prefetch_data(self):
        self.provider.prefetch_data()
        assert "AAPL" in self.provider.data
        assert "GOOG" in self.provider.data
        assert isinstance(self.provider.data["AAPL"][0], PricePoint)

    def test_lazy_prefetch_single_ticker_new(self):
        rng = PrefetchRange(datetime(2020, 1, 1), datetime(2020, 1, 2))
        self.provider.lazy_prefetch_single_ticker("AAPL", rng)
        assert "AAPL" in self.provider.data_to_prefetch
        assert self.provider.data_to_prefetch["AAPL"] == rng

    def test_lazy_prefetch_single_ticker_extend(self):
        rng1 = PrefetchRange(datetime(2020, 1, 2), datetime(2020, 1, 3))
        rng2 = PrefetchRange(datetime(2020, 1, 1), datetime(2020, 1, 4))
        self.provider.lazy_prefetch_single_ticker("AAPL", rng1)
        self.provider.lazy_prefetch_single_ticker("AAPL", rng2)
        result = self.provider.data_to_prefetch["AAPL"]
        assert result.min_time == datetime(2020, 1, 1)
        assert result.max_time == datetime(2020, 1, 4)

    def test_get_price_success(self):
        self.provider.prefetch_data()
        price = self.provider.get_price("AAPL", datetime(2020, 1, 1))
        assert price == Decimal("100.0")

    def test_get_price_no_prefetch(self):
        with pytest.raises(ValueError):
            self.provider.get_price("AAPL", datetime(2020, 1, 1))

    def test_get_price_ticker_not_prefetched(self):
        self.provider.prefetch_data()
        with pytest.raises(ValueError):
            self.provider.get_price("MSFT", datetime(2020, 1, 1))


class TestPriceSelectStrategy:
    def setup_method(self):
        self.strategy = PriceSelectStrategy()

    @pytest.mark.parametrize(
        "prices, time_at, expected",
        [
            # Closest is at base
            ([
                PricePoint(price=Decimal('100.0'), date_at=datetime(2020, 1, 1, 11, 50, 0)),
                PricePoint(price=Decimal('110.0'), date_at=datetime(2020, 1, 1, 12, 0, 0)),
                PricePoint(price=Decimal('120.0'), date_at=datetime(2020, 1, 1, 12, 10, 0)),
            ], datetime(2020, 1, 1, 12, 0, 0), Decimal('110.0')),
            # Closest is +2 minutes
            ([
                PricePoint(price=Decimal('100.0'), date_at=datetime(2020, 1, 1, 11, 55, 0)),
                PricePoint(price=Decimal('200.0'), date_at=datetime(2020, 1, 1, 12, 2, 0)),
            ], datetime(2020, 1, 1, 12, 0, 0), Decimal('200.0')),
            # Equal distance, picks first
            ([
                PricePoint(price=Decimal('100.0'), date_at=datetime(2020, 1, 1, 11, 55, 0)),
                PricePoint(price=Decimal('200.0'), date_at=datetime(2020, 1, 1, 12, 5, 0)),
            ], datetime(2020, 1, 1, 12, 0, 0), Decimal('100.0')),
        ]
    )
    def test_select_parametrized(self, prices, time_at, expected):
        result = self.strategy.select(prices, time_at)
        assert result == expected

    def test_select_empty_list(self):
        with pytest.raises(ValueError):
            self.strategy.select([], datetime(2020, 1, 1))


class TestPrefetchStrategy:
    @pytest.mark.parametrize(
        "samples,min_time,max_time,expected_unit,int_multiplier",
        [
            (5, datetime(2020, 1, 1), datetime(2020, 1, 6), "d", 1),
            (10, datetime(2020, 1, 1), datetime(2020, 1, 2), "h", 2),
            (2, datetime(2020, 1, 1, 0, 0), datetime(2020, 1, 1, 0, 10), "m", 5),
            (3, datetime(2020, 1, 1, 0, 0), datetime(2020, 1, 1, 0, 0, 30), "s", 10),
        ],
    )
    def test_calculate_intervals_parametrized(
        self, samples, min_time, max_time, expected_unit, int_multiplier
    ):
        strategy = PrefetchStrategy(samples=samples)
        prices_to_prefetch = [("AAPL", max_time, min_time)]
        result = strategy.calculate(prices_to_prefetch)
        assert result == [
            FetcherData(
                ticker="AAPL",
                min_time=min_time,
                max_time=max_time,
                interval=expected_unit,
                interval_multiplier=int_multiplier,
            )
        ]

    def test_calculate_multiple_tickers(self):
        strategy = PrefetchStrategy(samples=3)
        min_time = datetime(2021, 1, 1)
        max_time = datetime(2021, 1, 4)
        prices_to_prefetch = [
            ("AAPL", max_time, min_time),
            ("GOOG", max_time + timedelta(days=1), min_time),
        ]
        result = strategy.calculate(prices_to_prefetch)
        assert len(result) == 2
        tickers = {fd.ticker for fd in result}
        assert tickers == {"AAPL", "GOOG"}