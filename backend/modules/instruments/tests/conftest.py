from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from modules.instruments.schemas import (InstrumentBasicInfoSchema,
                                         InstrumentDetailedInfoSchema)
from modules.prices.schemas import InstrumentPriceSchema

instrument_basic_info = [
    InstrumentBasicInfoSchema(
        ticker="AAPL",
        name="Apple Inc.",
        currency="USD",
        current_price=Decimal("180.5"),
        previous_close=Decimal("178.3"),
        day_change=Decimal("2.2"),
        day_change_percent=Decimal("1.23"),
        market_cap=Decimal("2900000000000"),
        volume=100000000,
        sector="Technology",
        industry="Consumer Electronics",
        country="United States",
    ),
    InstrumentBasicInfoSchema(
        ticker="MSFT",
        name="Microsoft Corporation",
        currency="USD",
        current_price=Decimal("330.7"),
        previous_close=Decimal("331.2"),
        day_change=Decimal("-0.5"),
        day_change_percent=Decimal("-0.15"),
        market_cap=Decimal("2500000000000"),
        volume=30000000,
        sector="Technology",
        industry="Software",
        country="United States",
    ),
]

instrument_detail_info = InstrumentDetailedInfoSchema(
    ticker="AAPL",
    name="Apple Inc.",
    currency="USD",
    current_price=Decimal("180.5"),
    previous_close=Decimal("178.3"),
    day_change=Decimal("2.2"),
    day_change_percent=Decimal("1.23"),
    market_cap=Decimal("2900000000000"),
    volume=100000000,
    sector="Technology",
    industry="Consumer Electronics",
    country="United States",
    description="Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
    website="https://www.apple.com",
    logo_url="https://logo.clearbit.com/apple.com",
    exchange="NASDAQ",
    fifty_two_week_low=Decimal("150.1"),
    fifty_two_week_high=Decimal("199.6"),
    trailing_pe=Decimal("30.5"),
    forward_pe=Decimal("28.3"),
    dividend_yield=Decimal("0.0058"),
    business_summary="Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod.",
)

ticker_info = {
    "symbol": instrument_detail_info.ticker,
    "shortName": instrument_detail_info.name,
    "currency": instrument_detail_info.currency,
    "currentPrice": float(instrument_detail_info.current_price),
    "previousClose": float(instrument_detail_info.previous_close),
    "marketCap": int(instrument_detail_info.market_cap),
    "volume": instrument_detail_info.volume,
    "sector": instrument_detail_info.sector,
    "industry": instrument_detail_info.industry,
    "country": instrument_detail_info.country,
    "longBusinessSummary": instrument_detail_info.description,
    "website": instrument_detail_info.website,
    "logo_url": instrument_detail_info.logo_url,
    "exchange": instrument_detail_info.exchange,
    "fiftyTwoWeekLow": float(instrument_detail_info.fifty_two_week_low),
    "fiftyTwoWeekHigh": float(instrument_detail_info.fifty_two_week_high),
    "trailingPE": float(instrument_detail_info.trailing_pe),
    "forwardPE": float(instrument_detail_info.forward_pe),
    "dividendYield": float(instrument_detail_info.dividend_yield),
    "earningsTimestamp": datetime(2023, 1, 1, 1, 0).timestamp(),
}

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
        mock_ticker.return_value = mock_instance
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
