from typing import cast
import yfinance
from datetime import datetime
from modules.prices.helpers import TimeInterval
from modules.prices.errors import UnknownTickerError
from modules.prices.dtos import InstrumentPriceDTO
from pandas import DataFrame, Timestamp

class YfinanceRepository:
    def get_instrument_price_for_timeperiod(self, instrument: str, start_date: datetime, end_date: datetime, interval: TimeInterval) -> list[InstrumentPriceDTO]:
        try:
            print(f"printing results for {instrument} from {start_date} to {end_date} with interval {interval.value}")
            ticker: yfinance.Ticker = yfinance.Ticker(instrument.lower())
            history: DataFrame = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval.value
            )

            if history.empty:
                raise UnknownTickerError(instrument)
            
            return self._covert_prices_to_dto(history, instrument)

        except Exception as  e:
            print(e)
            raise UnknownTickerError(instrument)
        
        
    def _covert_prices_to_dto(self, dataframe: DataFrame, instrument: str) -> list[InstrumentPriceDTO]:
        prices = []
        for index, row in dataframe.iterrows():
            ts: Timestamp = cast(Timestamp, index)
            prices.append(InstrumentPriceDTO(
                timestamp=ts.to_pydatetime(),
                ticker=instrument.upper(),
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=float(row['Volume'])
            ))
        return prices