from datetime import datetime
from decimal import Decimal
from modules.instruments.models import Instrument
from modules.authentication.tests.conftest import user


class PriceRepositoryMock:
    raise_exception_on_miss = False

    def __init__(self):
        self._prices: dict[tuple[Instrument, datetime], Decimal] = {}

    def get_prices_average_hl(
        self, tickers: list[Instrument], date_at: datetime
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

    def set_price(self, ticker: Instrument, date_at: datetime, price: Decimal):
        self._prices[(ticker, date_at)] = Decimal(price)
