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

ticker_info = {
    "symbol": "AAPL",
    "shortName": "Apple Inc.",
    "description": "Example company specializing in consumer electronics.",
    "website": "https://www.example.com",
    "logo_url": "https://www.example.com/logo.png",
    "exchange": "NASDAQ",
    "currentPrice": "180.50",
    "fiftyTwoWeekLow": "120.50",
    "fiftyTwoWeekHigh": "198.75",
    "trailingPE": "28.3",
    "forwardPE": "25.7",
    "dividendYield": "0.006",
    "earningsDate": datetime(2024, 7, 25),
    "longBusinessSummary": "The company designs, manufactures, and markets smartphones, computers, and related services.",
    "currency": "USD",
    "previousClose": "179.50",
    "marketCap": "3000000000000",
    "volume": 1000000,
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "country": "United States",
}

msft_ticker_info = {
    "symbol": "MSFT",
    "shortName": "Microsoft Corporation",
    "description": "Example company specializing in software.",
    "website": "https://www.microsoft.com",
    "logo_url": "https://www.microsoft.com/logo.png",
    "exchange": "NASDAQ",
    "currentPrice": "400.50",
    "fiftyTwoWeekLow": "320.50",
    "fiftyTwoWeekHigh": "450.75",
    "trailingPE": "35.3",
    "forwardPE": "32.7",
    "dividendYield": "0.008",
    "earningsDate": datetime(2024, 7, 25),
    "longBusinessSummary": "The company develops and supports software, services, and devices.",
    "currency": "USD",
    "previousClose": "395.50",
    "marketCap": "3000000000000",
    "volume": 2000000,
    "sector": "Technology",
    "industry": "Software",
    "country": "United States",
}


@pytest.fixture
def mock_yfinance_ticker():
    with patch("yfinance.Ticker") as mock_ticker:
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame(
            ticker_history["history"],
            index=[pd.Timestamp(ticker_history["index"])],
        )
        mock_instance.major_holders = pd.DataFrame(major_holders)
        mock_instance.institutional_holders = pd.DataFrame(institutional_holders)
        mock_instance.recommendations = pd.DataFrame(recommendations)
        mock_instance.info = ticker_info
        mock_ticker.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_yfinance_tickers():
    with patch("yfinance.Tickers") as mock_tickers:
        mock_instance = MagicMock()
        mock_instance.tickers = {
            "AAPL": MagicMock(info=ticker_info),
            "MSFT": MagicMock(info=msft_ticker_info),
        }
        mock_tickers.return_value = mock_instance
        yield mock_instance
