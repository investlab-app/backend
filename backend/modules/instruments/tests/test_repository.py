from decimal import Decimal

import pytest

from modules.instruments.exceptions import FetchInstrumentInfoException
from modules.instruments.repositories import YfinanceRepository
from modules.instruments.schemas import (
    InstrumentBasicInfoSchema,
    InstrumentDetailedInfoSchema,
)


def test_get_basic_instrument_info_success(mock_yfinance_tickers):
    repo = YfinanceRepository()
    tickers = ["AAPL", "MSFT"]
    result = repo.get_instruments_info(tickers)
    assert isinstance(result, list)
    assert all(isinstance(item, InstrumentBasicInfoSchema) for item in result)
    assert len(result) == 2
    assert result[0].ticker == "AAPL"
    assert result[1].ticker == "MSFT"


def test_raises_get_basic_instrument_info_invalid_ticker():
    repo = YfinanceRepository()
    tickers = ["invalid"]
    with pytest.raises(FetchInstrumentInfoException):
        repo.get_instruments_info(tickers)


def test_get_basic_instrument_info_empty_ticker(
    mock_yfinance_empty_history_ticker,
):
    repo = YfinanceRepository()
    tickers = []
    result = repo.get_instruments_info(tickers)
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_detailed_instrument_info_success(
    mock_yfinance_ticker,
):
    repo = YfinanceRepository()
    ticker = "AAPL"
    result = repo.get_instrument_detailed_info(ticker)
    assert isinstance(result, InstrumentDetailedInfoSchema)
    assert result.current_price == Decimal("180.5")
    assert result.major_holders is not None
    assert result.institutional_holders is not None
    assert result.analyst_recommendations is not None


def test_get_detailed_instrument_info_invalid_ticker():
    repo = YfinanceRepository()
    ticker = "invalid"
    with pytest.raises(FetchInstrumentInfoException):
        repo.get_instrument_detailed_info(ticker)


def test_get_detailed_instrument_info_missing_data(
    mock_yfinance_ticker,
):
    repo = YfinanceRepository()
    ticker_str = "AAPL"
    result = repo.get_instrument_detailed_info(ticker_str)
    assert isinstance(result, InstrumentDetailedInfoSchema)
    assert (
        result.description
        == (
            "The company designs, manufactures, and markets smartphones, computers, "
            "and related services."
        )
    )
