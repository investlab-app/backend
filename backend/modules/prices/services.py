from datetime import datetime

from rest_framework import exceptions

from modules.prices.constants import TimeInterval
from modules.prices.errors import (
    IllegalDateOrderException,
    InvalidTimeIntervalException,
)
from modules.prices.repositories import YfinanceRepository
from modules.prices.schemas import InstrumentPriceSchema


class PricesServiceMinimal:
    def __init__(self):
        self._repository = YfinanceRepository()

    def get_instrument_price_for_timeperiod(
        self, instrument: str, start_date: datetime, end_date: datetime, interval: str
    ) -> list[InstrumentPriceSchema]:
        """
        Retrieves historical price data for a given financial instrument within a specified time range and interval.

        Args:
            instrument (str): The ticker symbol of the instrument (e.g., "AAPL").
            start_date (datetime): The starting datetime for the price data range.
            end_date (datetime): The ending datetime for the price data range.
            interval (str): The desired data interval (e.g., "1d", "1h").

        Returns:
            list[InstrumentPriceDTO]: A list of DTOs containing price information for each time point.

        Raises:
            ValidationError: If the start_date is after the end_date.
            APIException: If an error occurs while fetching data from the repository.
        """

        if start_date > end_date:
            raise IllegalDateOrderException()
        return self._repository.get_instrument_price(
            instrument,
            start_date,
            end_date,
            self._parse_time_interval(interval.lower()),
        )

    def _parse_time_interval(self, value: str) -> TimeInterval:
        try:
            return TimeInterval(value)
        except ValueError:
            raise InvalidTimeIntervalException(
                f"Invalid time interval, valid intervals are: {", ".join([ti.value for ti in TimeInterval])}"
            )
