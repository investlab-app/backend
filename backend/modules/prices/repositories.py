from datetime import datetime
from decimal import Decimal
from typing import cast

import yfinance
from pandas import DataFrame, Timestamp

from modules.prices.constants import YFinanceTimeInterval
from modules.prices.exceptions import FetchPriceException
from modules.prices.schemas import InstrumentPriceSchema


class YfinanceRepository:
    @staticmethod
    def get_instrument_price_history(
        instrument: str,
        start_date: datetime,
        end_date: datetime,
        interval: YFinanceTimeInterval,
    ) -> list[InstrumentPriceSchema]:
        """
        Retrieves historical price data for a financial instrument within a specified date range and interval.
        
        Args:
            instrument: The ticker symbol of the financial instrument.
            start_date: The start date for the historical data.
            end_date: The end date for the historical data.
            interval: The time interval for the historical data.
        
        Returns:
            A list of InstrumentPriceSchema objects representing the instrument's historical prices.
        
        Raises:
            FetchPriceException: If data retrieval fails or no data is available for the given ticker.
        """
        try:
            y_ticker = yfinance.Ticker(instrument.lower())
            history = y_ticker.history(
                start=start_date, end=end_date, interval=interval.value
            )
        except Exception as e:
            raise FetchPriceException(str(e)) from e

        if history.empty:
            raise FetchPriceException(f"History is empty for the ticker {instrument}")
        return YfinanceRepository._convert_prices_to_schema(history)

    @staticmethod
    def _convert_prices_to_schema(dataframe: DataFrame) -> list[InstrumentPriceSchema]:
        prices = []
        for index, row in dataframe.iterrows():
            ts = cast(Timestamp, index)
            prices.append(
                InstrumentPriceSchema(
                    timestamp=ts.to_pydatetime(),
                    open=Decimal(row["Open"]),
                    high=Decimal(row["High"]),
                    low=Decimal(row["Low"]),
                    close=Decimal(row["Close"]),
                )
            )
        return prices
