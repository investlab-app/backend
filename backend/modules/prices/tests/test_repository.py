from datetime import datetime

import pytest

from modules.prices.constants import TimeInterval
from modules.prices.errors import FetchPriceException
from modules.prices.repositories import YfinanceRepository
from modules.prices.schemas import InstrumentPriceSchema


def test_get_instrument_price_success(
    mock_yfinance_ticker, expected_result_from_ticker
):
    repo = YfinanceRepository()
    start = datetime(2024, 4, 1)
    end = datetime(2024, 4, 2)
    interval = TimeInterval.ONE_MINUTE

    result = repo.get_instrument_price("AAPL", start, end, interval)

    assert isinstance(result, list)
    assert all(isinstance(item, InstrumentPriceSchema) for item in result)
    assert result == expected_result_from_ticker


def test_raises_unknown_ticker_error_on_empty_history(
    mock_yfinance_empty_history_ticker,
):
    repo = YfinanceRepository()
    with pytest.raises(FetchPriceException):
        repo.get_instrument_price(
            instrument="AAPL",
            start_date=datetime(2024, 4, 1),
            end_date=datetime(2024, 4, 30),
            interval=TimeInterval.ONE_DAY,
        )


def test_raises_unknown_ticker_error_on_exception(mock_yfinance_invalid_ticker):
    repo = YfinanceRepository()

    with pytest.raises(FetchPriceException):
        repo.get_instrument_price(
            instrument="invalid",
            start_date=datetime(2024, 4, 1),
            end_date=datetime(2024, 4, 30),
            interval=TimeInterval.ONE_DAY,
        )
