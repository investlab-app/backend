from datetime import datetime
from decimal import Decimal
from typing import TypedDict

from config.logging import get_logger
from config.utils import parse_time_interval
from modules.prices.exceptions import InvalidTimeIntervalException
from modules.prices.repositories import YfinanceRepository
from modules.prices.schemas import (
    InstrumentPriceSchema,
)

logger = get_logger(__name__)


class PriceHistoryWithStats(TypedDict):
    data: list[InstrumentPriceSchema]
    min_price: Decimal
    max_price: Decimal


class PricesService:
    def __init__(self, repository: YfinanceRepository):
        self._repository = repository

    def get_instrument_price_history(
        self,
        instrument: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> PriceHistoryWithStats:
        """
        Retrieves historical price data for a given instrument.

        Retrieves price data with min and max price over the specified range.

        Args:
            instrument (str): The ticker symbol of the instrument (e.g., "AAPL").
            start_date (datetime): The starting datetime for the price data range.
            end_date (datetime): The ending datetime for the price data range.
            interval (str): The desired data interval (e.g., "1d", "1h").

        Returns:
            PriceRangeWithStats: dict with 'data' - list[InstrumentPriceSchema],
                'min_price', and 'max_price'

        Raises:
            ValidationError: If the start_date is after the end_date.
            APIException: If an error occurs while fetching data from the repository.
        """
        if start_date > end_date:
            raise InvalidTimeIntervalException(
                "Invalid date order, end date cannot preceed start date.",
            )
        data = self._repository.get_instrument_price_history(
            instrument,
            start_date,
            end_date,
            parse_time_interval(interval.lower()),
        )
        logger.debug("Got data: %s", data)
        min_price = min(d.low for d in data)
        max_price = max(d.high for d in data)

        return PriceHistoryWithStats(
            data=data,
            min_price=min_price,
            max_price=max_price,
        )
