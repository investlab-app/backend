from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

major_holders = {"Major Holder": ["Holder A"], "Shares": [1000]}

institutional_holders = {"Institutional Holder": ["Institution B"], "Shares": [2000]}

recommendations = {"Firm": ["Analyst C"], "To Grade": ["Buy"]}

ticker_history = {
    "history": {
        "Open": [100.0],
        "High": [110.0],
        "Low": [90.0],
        "Close": [105.0],
        "Volume": [1000],
        "Irrelevant_data": [8532],
    },
    "index": datetime(2024, 4, 1),
}


@pytest.fixture
def mock_yfinance_ticker():
    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame(
            ticker_history["history"],
            index=[pd.Timestamp(ticker_history["index"])],
        )
        mock_instance.major_holders.return_value = pd.DataFrame(major_holders)
        mock_instance.institutional_holders.return_value = pd.DataFrame(
            institutional_holders
        )
        mock_instance.recommendations.return_value = pd.DataFrame(recommendations)
        mock_ticker.return_value = mock_instance
        yield mock_instance
