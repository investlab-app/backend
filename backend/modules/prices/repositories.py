from datetime import datetime
from decimal import Decimal
from typing import cast

import yfinance
from pandas import DataFrame, Timestamp

from modules.prices.constants import TimeInterval
from modules.prices.errors import FetchPriceException
from modules.prices.schemas import InstrumentPriceSchema


class YfinanceRepository:
    @staticmethod
    def get_instrument_price(
        instrument: str,
        start_date: datetime,
        end_date: datetime,
        interval: TimeInterval,
    ) -> list[InstrumentPriceSchema]:
        """
        Fetches historical price data for a specified financial instrument using the yfinance library.

        Args:
            instrument (str): The ticker symbol of the instrument (e.g., "aapl").
            start_date (datetime): The start of the time period to retrieve data for.
            end_date (datetime): The end of the time period to retrieve data for.
            interval (TimeInterval): The time interval for the historical data (e.g., "ONE_MINUTE", "ONE_DAY").

        Returns:
            list[InstrumentPriceSchema]: A list of Pydantic models containing the instrument's historical prices.

        Raises:
            UnknownTickerException: If the ticker is invalid or no data is returned.
        """
        try:
            ticker = yfinance.Ticker(instrument.lower())
            history = ticker.history(
                start=start_date, end=end_date, interval=interval.value
            )

            if history.empty:
                raise FetchPriceException(
                    f"History is empty for the ticker {instrument}"
                )
            return YfinanceRepository._covert_prices_to_dto(history, instrument)

        except Exception as e:
            raise FetchPriceException(str(e))

    @staticmethod
    def _covert_prices_to_dto(
        dataframe: DataFrame, instrument: str
    ) -> list[InstrumentPriceSchema]:
        prices = []
        for index, row in dataframe.iterrows():
            ts = cast(Timestamp, index)
            prices.append(
                InstrumentPriceSchema(
                    timestamp=ts.to_pydatetime(),
                    ticker=instrument.upper(),
                    open=Decimal(row["Open"]),
                    high=Decimal(row["High"]),
                    low=Decimal(row["Low"]),
                    close=Decimal(row["Close"]),
                    volume=Decimal((row["Volume"])),
                )
            )
        return prices
