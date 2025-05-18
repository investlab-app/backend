import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from modules.prices.dtos import InstrumentPriceDTO
import pandas as pd

@pytest.fixture
def mock_yfinance_repository():
    with patch('modules.prices.services.YfinanceRepository') as MockRepo:
        mock_instance = MagicMock()
        mock_instance.get_instrument_price_for_timeperiod.return_value = [
            InstrumentPriceDTO(
                timestamp=datetime(2024, 4, 1, 0, 0, 0),
                ticker="AAPL",
                open=170.0,
                high=172.0,
                low=168.0,
                close=171.0,
                volume=1000000
            )
        ]
        MockRepo.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_yfinance_ticker():
    with patch("yfinance.Ticker") as MockTicker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame({
            "Open": [100.0],
            "High": [110.0],
            "Low": [90.0],
            "Close": [105.0],
            "Volume": [1000],
            "Irrelevant_data": [8532]
        }, index=[pd.Timestamp(datetime(2024, 4, 1))])
        MockTicker.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_yfinance_empty_history_ticker():
    with patch("yfinance.Ticker") as MockTicker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame()
        MockTicker.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_yfinance_invalid_ticker():
    with patch("yfinance.Ticker", side_effect=Exception("Some API failure")) as MockTicker:
        yield MockTicker    
    

@pytest.fixture
def expected_result_from_ticker():
    return [InstrumentPriceDTO(
        timestamp=datetime(2024, 4, 1),
        ticker="AAPL",
        open=100.0,
        high=110.0,
        low=90.0,
        close=105.0,
        volume=1000.0
    )]
