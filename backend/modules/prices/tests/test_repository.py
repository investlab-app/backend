from datetime import datetime
from modules.prices.errors import UnknownTickerError
from modules.prices.repositories import YfinanceRepository
from modules.prices.helpers import TimeInterval
from modules.prices.dtos import InstrumentPriceDTO
import pytest

def test_get_instrument_price_success(mock_yfinance_ticker, expected_result_from_ticker):
    repo = YfinanceRepository()
    start = datetime(2024, 4, 1)
    end = datetime(2024, 4, 2)
    interval = TimeInterval.ONE_MINUTE

    result = repo.get_instrument_price_for_timeperiod("AAPL", start, end, interval)

    assert isinstance(result, list)
    assert all(isinstance(item, InstrumentPriceDTO) for item in result)
    assert result == expected_result_from_ticker


def test_raises_unknown_ticker_error_on_empty_history(mock_yfinance_empty_history_ticker):
    repo = YfinanceRepository()
    with pytest.raises(UnknownTickerError):
        repo.get_instrument_price_for_timeperiod(
            instrument="AAPL",
            start_date=datetime(2024, 4, 1),
            end_date=datetime(2024, 4, 30),
            interval=TimeInterval.ONE_DAY
        )


def test_raises_unknown_ticker_error_on_exception(mock_yfinance_invalid_ticker):
    repo = YfinanceRepository()

    with pytest.raises(UnknownTickerError):
        repo.get_instrument_price_for_timeperiod(
            instrument="invalid",
            start_date=datetime(2024, 4, 1),
            end_date=datetime(2024, 4, 30),
            interval=TimeInterval.ONE_DAY
        )