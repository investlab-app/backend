import random
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

import faker
import pytest

from modules.authentication.tests.conftest import user  # noqa: F401
from modules.instruments.models import Instrument
from modules.instruments.tests.conftest import (
    create_fake_instrument,
    instruments_factory,
)
from modules.investors.tests.conftest import (
    create_fake_investor,
    investor_factory,
)
from modules.prices.schemas import PriceBar, PriceDaily, PriceDailySummary

fake = faker.Faker()


class PriceRepositoryMock:
    raise_exception_on_miss = False

    def __init__(self):
        self._prices: dict[tuple[Instrument, datetime], Decimal] = {}

    def set_price(self, ticker: Instrument, price, date_at=None):
        self._prices[(ticker, date_at)] = Decimal(price)

    def get_prices_at(
        self,
        tickers: list[Instrument],
        date_at: datetime | None = None,
    ) -> dict[Instrument, Decimal]:
        result = {}
        for ticker in tickers:
            key = (ticker, date_at)
            if key in self._prices:
                result[ticker] = self._prices[key]
            elif self.raise_exception_on_miss:
                raise ValueError(
                    f"Price for {ticker.ticker} at {date_at} not set in mock"
                )
            else:
                result[ticker] = Decimal(0)
        return result

    def get_prices(self, tickers: list[str]) -> list[PriceDailySummary] | None:
        result = []
        for ticker in tickers:
            instrument = Instrument.objects.filter(ticker=ticker).first()
            if not instrument:
                if self.raise_exception_on_miss:
                    raise ValueError(f"Instrument {ticker} not found in mock")
                else:
                    continue
            key = (instrument, None)
            if key in self._prices:
                price = self._prices[key]
            elif self.raise_exception_on_miss:
                raise ValueError(f"Price for {ticker} not set in mock")
            else:
                price = Decimal(0)

            price_daily = PriceDaily(
                open=Decimal("182.34"),
                high=Decimal("185.12"),
                low=Decimal("181.76"),
                close=Decimal("184.67"),
                volume=Decimal(52345678),
                volume_weighted_average_price=Decimal("183.45"),
            )
            price_summary = PriceDailySummary(
                ticker=ticker,
                daily_summary=price_daily,
                todays_change=Decimal("2.33"),
                todays_change_percent=Decimal("1.28"),
                last_updated=datetime(2025, 10, 6, 22, 41, 8, 579770),
            )
            result.append(price_summary)

        return result if result else None

    def get_prices_map(self, tickers: list[str]) -> dict[str, PriceDailySummary]:
        prices_list = self.get_prices(tickers)
        if prices_list is None:
            return {}
        return {price.ticker: price for price in prices_list}


class LatestPriceServiceMock:
    def __init__(self):
        self._prices: dict[tuple[Instrument, datetime], Decimal] = {}

    def set_price(self, ticker: Instrument, price, date_at=None):
        self._prices[(ticker, date_at)] = Decimal(price)

    def get_prices(self) -> dict[str, Decimal]:
        return {
            ticker.ticker: price
            for (ticker, _), price in self._prices.items()
        }

    def get_prices_default_dict(
        self, factory=lambda: Decimal(1)
    ) -> defaultdict[str, Decimal]:
        price_bars = self.get_prices()
        prices_dict = defaultdict(factory)
        prices_dict.update(price_bars)
        return prices_dict


def get_fake_ohlc(
    ticker: str,
    volume: Decimal | None = None,
    accumulated_volume: Decimal | None = None,
    official_open_price: Decimal | None = None,
    vwap: Decimal | None = None,
    open_: Decimal | None = None,
    close: Decimal | None = None,
    high: Decimal | None = None,
    low: Decimal | None = None,
    aggregate_vwap: Decimal | None = None,
    average_size: Decimal | None = None,
    start_timestamp: Decimal | None = None,
    end_timestamp: Decimal | None = None,
) -> dict:
    now_ms = int(time.time() * 1000)

    op = official_open_price or round(Decimal(random.uniform(0.4, 1.0)), 4)
    vw = vwap or round(op + Decimal(random.uniform(-0.01, 0.01)), 4)
    o = open_ or round(vw + Decimal(random.uniform(-0.002, 0.002)), 4)
    c = close or round(vw + Decimal(random.uniform(-0.002, 0.002)), 4)

    h = high or round(max(o, c) + Decimal(random.uniform(0, 0.002)), 4)
    low = low or round(min(o, c) - Decimal(random.uniform(0, 0.002)), 4)

    return {
        "symbol": ticker,
        "volume": volume or random.randint(1000, 10000),
        "accumulated_volume": accumulated_volume
        or random.randint(1_000_000, 10_000_000),
        "official_open_price": op,
        "vwap": vw,
        "open": o,
        "close": c,
        "high": h,
        "low": low,
        "aggregate_vwap": aggregate_vwap
        or round(op + Decimal(random.uniform(-0.02, 0.02)), 4),
        "average_size": average_size or random.randint(100, 1000),
        "start_timestamp": start_timestamp or now_ms - 1000,
        "end_timestamp": end_timestamp or now_ms,
    }


def get_fake_price_bar(
    timestamp: datetime | None = None,
    open_: Decimal | None = None,
    high: Decimal | None = None,
    low: Decimal | None = None,
    close: Decimal | None = None,
    volume: Decimal | None = None,
    transactions: int | None = None,
    volume_weighted_average_price: Decimal | None = None,
) -> PriceBar:
    if timestamp is None:
        timestamp = fake.past_datetime()
    if open_ is None:
        open_ = fake.pydecimal()
    if high is None:
        high = fake.pydecimal()
    if low is None:
        low = fake.pydecimal()
    if close is None:
        close = fake.pydecimal()
    if volume is None:
        volume = fake.pydecimal()
    if transactions is None:
        transactions = fake.pyint(min_value=0)
    if volume_weighted_average_price is None:
        volume_weighted_average_price = fake.pydecimal()

    return PriceBar(
        timestamp=timestamp,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        transactions=transactions,
        volume_weighted_average_price=volume_weighted_average_price,
    )
