from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from modules.prices.schemas import InstrumentPriceSchema

instrument_price_history = [
    InstrumentPriceSchema(
        timestamp=datetime(2024, 4, 1, 0, 0, 0),
        open=Decimal("170.0"),
        high=Decimal("172.0"),
        low=Decimal("168.0"),
        close=Decimal("171.0"),
    ),
    InstrumentPriceSchema(
        timestamp=datetime(2024, 4, 2, 0, 0, 0),
        open=Decimal("170.7"),
        high=Decimal("170.8"),
        low=Decimal("169.0"),
        close=Decimal("170.1"),
    ),
]


@pytest.fixture
def mock_yfinance_repository():
    with patch("modules.prices.services.YfinanceRepository") as mock_repo:
        mock_instance = MagicMock()
        mock_instance.get_instrument_price_history.return_value = (
            instrument_price_history
        )
        mock_repo.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_yfinance_empty_history_ticker():
    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_yfinance_invalid_ticker():
    with patch(
        "yfinance.Ticker", side_effect=Exception("Some API failure")
    ) as mock_ticker:
        yield mock_ticker


@pytest.fixture
def expected_result_from_ticker():
    return [
        InstrumentPriceSchema(
            timestamp=datetime(2024, 4, 1),
            open=Decimal("100.0"),
            high=Decimal("110.0"),
            low=Decimal("90.0"),
            close=Decimal("105.0"),
        )
    ]
