import random
from datetime import datetime
from decimal import Decimal
from typing import TypedDict

import asyncio

from modules.prices.constants import YFinanceTimeInterval
from modules.prices.exceptions import InvalidTimeIntervalException
from modules.prices.repositories import YfinanceRepository
from modules.prices.schemas import InstrumentPriceSchema


class PriceHistoryWithStats(TypedDict):
    data: list[InstrumentPriceSchema]
    min_price: Decimal
    max_price: Decimal


class PricesServiceMinimal:
    def __init__(self):
        self._repository = YfinanceRepository()

    def get_instrument_price_history(
        self, instrument: str, start_date: datetime, end_date: datetime, interval: str
    ) -> PriceHistoryWithStats:
        """
        Retrieves historical price data for a given instrument with min and max price over the range.

        Args:
            instrument (str): The ticker symbol of the instrument (e.g., "AAPL").
            start_date (datetime): The starting datetime for the price data range.
            end_date (datetime): The ending datetime for the price data range.
            interval (str): The desired data interval (e.g., "1d", "1h").

        Returns:
            PriceRangeWithStats: dict with 'data' - list[InstrumentPriceSchema], 'min_price', and 'max_price'

        Raises:
            ValidationError: If the start_date is after the end_date.
            APIException: If an error occurs while fetching data from the repository.
        """

        if start_date > end_date:
            raise InvalidTimeIntervalException(
                "Invalid date order, end date cannot preceed start date."
            )
        data = self._repository.get_instrument_price_history(
            instrument,
            start_date,
            end_date,
            self._parse_time_interval(interval.lower()),
        )
        min_price = min(d.low for d in data)
        max_price = max(d.high for d in data)

        return PriceHistoryWithStats(
            data=data, min_price=min_price, max_price=max_price
        )

    @staticmethod
    def _parse_time_interval(value: str) -> YFinanceTimeInterval:
        try:
            return YFinanceTimeInterval(value)
        except ValueError as e:
            raise InvalidTimeIntervalException(
                f"Invalid time interval, valid intervals are: {", ".join([ti.value for ti in YFinanceTimeInterval])}"
            ) from e

class LivePrices:

    def __init__(self):
        self.handlers = []
        self.instruments: set[str] = set()
        self.task: asyncio.Task | None = None

    def create_task(self) -> None:
        if self.instruments and self.handlers and not self.task:
            self.task = asyncio.create_task(self.run())

    def cancel_task(self) -> None:
        if self.task:
            self.task.cancel()
            self.task = None

    def restart_task(self) -> None:
        self.cancel_task()
        self.create_task()

    def add_instruments(self, instruments: set[str]) -> None:
        self.instruments.update(instruments)
        self.restart_task()

    def remove_instruments(self, instruments: set[str]) -> None:
        self.instruments.difference_update(instruments)
        self.restart_task()

    def add_handler(self, handler) -> None:
        self.handlers.append(handler)
        self.create_task()

    def remove_handler(self, handler) -> None:
        self.handlers.remove(handler)
        self.cancel_task()

    # # Uncomment this when you want to use yfinance
    # def yfinance_handler(self, prices: dict[str, float]) -> None:
    #     asyncio.create_task(
    #         asyncio.gather(*(handler(prices) for handler in self.handlers), return_exceptions=True)
    #     )
    #
    # async def run(self) -> None:
    #     yfinance.Tickers(self.instruments).live(self.yfinance_handler)

    async def run(self) -> None:
        while self.instruments:
            await asyncio.sleep(1)
            prices = {instrument: random.uniform(100, 500) for instrument in self.instruments}
            await asyncio.gather(*(handler(prices) for handler in self.handlers), return_exceptions=True)
