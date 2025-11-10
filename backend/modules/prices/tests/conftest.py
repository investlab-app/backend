from datetime import datetime
from decimal import Decimal
import random
import time

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
from modules.prices.schemas import PriceDaily, PriceDailySummary


class PriceRepositoryMock:
    raise_exception_on_miss = False

    def __init__(self):
        self._prices: dict[tuple[Instrument, datetime], Decimal] = {}

    def set_price(self, ticker: Instrument, price: Decimal, date_at=None):
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
                current_price=price,
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


import time
import random
from decimal import Decimal


def get_fake_ohlc(
    ticker: str,
    volume: Decimal = None,
    accumulated_volume: Decimal = None,
    official_open_price: Decimal = None,
    vwap: Decimal = None,
    open: Decimal = None,
    close: Decimal = None,
    high: Decimal = None,
    low: Decimal = None,
    aggregate_vwap: Decimal = None,
    average_size: Decimal = None,
    start_timestamp: Decimal = None,
    end_timestamp: Decimal = None,
) -> dict:
    now_ms = int(time.time() * 1000)

    op = official_open_price or round(random.uniform(0.4, 1.0), 4)
    vw = vwap or round(op + random.uniform(-0.01, 0.01), 4)
    o = open or round(vw + random.uniform(-0.002, 0.002), 4)
    c = close or round(vw + random.uniform(-0.002, 0.002), 4)

    h = high or round(max(o, c) + random.uniform(0, 0.002), 4)
    l = low or round(min(o, c) - random.uniform(0, 0.002), 4)

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
        "low": l,
        "aggregate_vwap": aggregate_vwap or round(op + random.uniform(-0.02, 0.02), 4),
        "average_size": average_size or random.randint(100, 1000),
        "start_timestamp": start_timestamp or now_ms - 1000,
        "end_timestamp": end_timestamp or now_ms,
    }
