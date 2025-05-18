from datetime import datetime
from typing import cast

import yfinance
from pandas import DataFrame, Timestamp

from modules.prices.dtos import InstrumentPriceDTO
from modules.prices.errors import UnknownTickerError
from modules.prices.helpers import TimeInterval


class YfinanceRepository:
    def get_instrument_price_for_timeperiod(
        self,
        instrument: str,
        start_date: datetime,
        end_date: datetime,
        interval: TimeInterval,
    ) -> list[InstrumentPriceDTO]:
        """
        Fetches historical price data for a specified financial instrument using the yfinance library.

        Args:
            instrument (str): The ticker symbol of the instrument (e.g., "aapl").
            start_date (datetime): The start of the time period to retrieve data for.
            end_date (datetime): The end of the time period to retrieve data for.
            interval (TimeInterval): The time interval for the historical data (e.g., "ONE_MINUTE", "ONE_DAY").

        Returns:
            list[InstrumentPriceDTO]: A list of data transfer objects containing the instrument's historical prices.

        Raises:
            UnknownTickerError: If the ticker is invalid or no data is returned.
        """

        try:
            ticker: yfinance.Ticker = yfinance.Ticker(instrument.lower())
            history: DataFrame = ticker.history(
                start=start_date, end=end_date, interval=interval.value
            )

            if history.empty:
                raise UnknownTickerError(instrument)
            return self._covert_prices_to_dto(history, instrument)

        except Exception as e:
            raise UnknownTickerError(instrument)

    def _covert_prices_to_dto(
        self, dataframe: DataFrame, instrument: str
    ) -> list[InstrumentPriceDTO]:
        prices = []
        for index, row in dataframe.iterrows():
            ts: Timestamp = cast(Timestamp, index)
            prices.append(
                InstrumentPriceDTO(
                    timestamp=ts.to_pydatetime(),
                    ticker=instrument.upper(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                )
            )
        return prices
