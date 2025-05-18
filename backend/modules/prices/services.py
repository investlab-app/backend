from datetime import datetime

from rest_framework import exceptions

from modules.prices.dtos import InstrumentPriceDTO
from modules.prices.helpers import TimeInterval
from modules.prices.repositories import YfinanceRepository


class PricesServiceMinimal:
    def __init__(self):
        self._repository = YfinanceRepository()

    def get_instrument_price_for_timeperiod(
        self, instrument: str, start_date: datetime, end_date: datetime, interval: str
    ) -> list[InstrumentPriceDTO]:
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
            raise exceptions.ValidationError("Start date cannot be after the end date.")
        try:
            return self._repository.get_instrument_price_for_timeperiod(
                instrument,
                start_date,
                end_date,
                self._parse_time_interval(interval.lower()),
            )
        except Exception as e:
            raise exceptions.APIException("Failed to retrieve instrument price data.")

    def _parse_time_interval(self, value: str) -> TimeInterval:
        try:
            return TimeInterval(value)
        except ValueError as e:
            raise exceptions.ValidationError(str(e))
