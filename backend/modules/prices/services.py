from modules.prices.repositories import YfinanceRepository
from datetime import datetime
from modules.prices.helpers import TimeInterval
from modules.prices.dtos import InstrumentPriceDTO
from rest_framework import exceptions


class PricesServiceMinimal:
    def __init__(self):
        self._repository = YfinanceRepository()

    def get_instrument_price_for_timeperiod(self, instrument: str,  start_date: datetime, end_date: datetime, interval: str) -> list[InstrumentPriceDTO]:
        if start_date > end_date:
            raise exceptions.ValidationError("Start date cannot be after the end date.")
        try:
            return self._repository.get_instrument_price_for_timeperiod(instrument, start_date, end_date, self._parse_time_interval(interval.lower()))
        except Exception as e:
            print(f"Error fetching price data: {e}")
            raise exceptions.APIException("Failed to retrieve instrument price data.")

    def _parse_time_interval(self, value: str) -> TimeInterval:
        try:
            return TimeInterval(value)
        except ValueError as e:
            raise exceptions.ValidationError(str(e))