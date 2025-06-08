from datetime import datetime

import pytest

from modules.prices.constants import YFinanceTimeInterval
from modules.prices.exceptions import FetchPriceException
from modules.prices.repositories import YfinanceRepository


def test_raises_fetch_price_exception_on_empty_history(
    mock_yfinance_empty_history_ticker,
):
    repo = YfinanceRepository()
    with pytest.raises(FetchPriceException):
        repo.get_instrument_price_history(
            instrument="AAPL",
            start_date=datetime(2024, 4, 1),
            end_date=datetime(2024, 4, 30),
            interval=YFinanceTimeInterval.ONE_DAY,
        )


def test_raises_fetch_price_exception_on_invalid_instrument():
    repo = YfinanceRepository()
    with pytest.raises(FetchPriceException):
        repo.get_instrument_price_history(
            instrument="invalid",
            start_date=datetime(2024, 4, 1),
            end_date=datetime(2024, 4, 30),
            interval=YFinanceTimeInterval.ONE_DAY,
        )


