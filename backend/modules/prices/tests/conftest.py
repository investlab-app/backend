from datetime import datetime
from decimal import Decimal

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
