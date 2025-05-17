import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from modules.prices.dtos import InstrumentPriceDTO


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
