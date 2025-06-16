from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from modules.instruments.exceptions import (
    FetchInstrumentInfoException,
    FetchInstrumentNewsException,
)
from modules.instruments.repositories import InstrumentsRepository
from modules.instruments.schemas import (
    InstrumentBasicInfoSchema,
    InstrumentDetailedInfoSchema,
    NewsContent,
    NewsFinance,
    NewsItem,
    NewsMetadata,
    NewsPremiumFinance,
    NewsProvider,
    NewsThumbnail,
    NewsThumbnailResolution,
    NewsUrl,
)

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
    "longBusinessSummary": (
        "The company designs, manufactures, and markets smartphones, computers, "
        "and related services."
    ),
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
    "longBusinessSummary": (
        "The company develops and supports software, services, and devices."
    ),
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


@pytest.fixture
def mock_instruments_repository():
    class MockInstrumentsRepository(InstrumentsRepository):
        def __init__(self):
            super().__init__(available_instruments=["AAPL", "MSFT", "GOOG"])

        def get_instruments_info(
            self, tickers: list[str]
        ) -> list[InstrumentBasicInfoSchema]:
            return [
                InstrumentBasicInfoSchema(
                    ticker="AAPL",
                    name="Apple Inc.",
                    currency="USD",
                    current_price=Decimal("180.5"),
                    previous_close=Decimal("179.5"),
                    day_change=Decimal("1.0"),
                    day_change_percent=Decimal("0.56"),
                    market_cap=Decimal("2800000000000"),
                    volume=1000000,
                    sector="Technology",
                    industry="Consumer Electronics",
                    country="US",
                ),
                InstrumentBasicInfoSchema(
                    ticker="MSFT",
                    name="Microsoft Corporation",
                    currency="USD",
                    current_price=Decimal("380.5"),
                    previous_close=Decimal("379.5"),
                    day_change=Decimal("1.0"),
                    day_change_percent=Decimal("0.26"),
                    market_cap=Decimal("2800000000000"),
                    volume=2000000,
                    sector="Technology",
                    industry="Software",
                    country="US",
                ),
            ]

        def get_instrument_detailed_info(
            self, ticker: str
        ) -> InstrumentDetailedInfoSchema:
            if ticker == "INVALID":
                raise FetchInstrumentInfoException("Invalid ticker")

            return InstrumentDetailedInfoSchema(
                ticker="AAPL",
                name="Apple Inc.",
                currency="USD",
                current_price=Decimal("180.5"),
                previous_close=Decimal("179.5"),
                day_change=Decimal("1.0"),
                day_change_percent=Decimal("0.56"),
                market_cap=Decimal("2800000000000"),
                volume=1000000,
                sector="Technology",
                industry="Consumer Electronics",
                country="US",
                description=(
                    "Apple Inc. designs, manufactures, and markets smartphones, "
                    "personal computers, tablets, wearables, and accessories worldwide."
                ),
                website="https://www.apple.com",
                logo_url="https://logo.clearbit.com/apple.com",
                exchange="NMS",
                fifty_two_week_low=Decimal("120.0"),
                fifty_two_week_high=Decimal("200.0"),
                trailing_pe=Decimal("25.0"),
                forward_pe=Decimal("24.0"),
                dividend_yield=Decimal("0.5"),
                earnings_date=datetime.now(),
                major_holders={"data": [["Institution", "50%"], ["Individual", "50%"]]},
                institutional_holders=[{"Holder": "Vanguard", "Shares": "1000000"}],
                analyst_recommendations={
                    "data": [["Buy", "10"], ["Hold", "5"], ["Sell", "1"]]
                },
            )

        def get_news(self, ticker: str) -> list[NewsItem]:
            if ticker == "INVALID":
                raise FetchInstrumentNewsException("Invalid ticker")

            return [
                NewsItem(
                    id="news1",
                    content=NewsContent(
                        id="content1",
                        content_type="NEWS",
                        title="Apple announces new iPhone",
                        description="Apple has announced its latest iPhone model",
                        summary="New iPhone announcement",
                        pub_date=datetime.now(),
                        display_time="2024-03-20T10:00:00Z",
                        is_hosted=False,
                        bypass_modal=False,
                        preview_url="https://example.com/preview",
                        thumbnail=NewsThumbnail(
                            original_url="https://example.com/image.jpg",
                            original_width=800,
                            original_height=600,
                            caption="iPhone image",
                            resolutions=[
                                NewsThumbnailResolution(
                                    url="https://example.com/image_small.jpg",
                                    width=400,
                                    height=300,
                                    tag="small",
                                )
                            ],
                        ),
                        provider=NewsProvider(
                            display_name="Reuters", url="https://reuters.com"
                        ),
                        canonical_url=NewsUrl(
                            url="https://reuters.com/apple-news",
                            site="reuters.com",
                            region="US",
                            lang="en",
                        ),
                        click_through_url=NewsUrl(
                            url="https://reuters.com/apple-news",
                            site="reuters.com",
                            region="US",
                            lang="en",
                        ),
                        metadata=NewsMetadata(editors_pick=True),
                        finance=NewsFinance(
                            premium_finance=NewsPremiumFinance(
                                is_premium_news=False, is_premium_free_news=True
                            )
                        ),
                        storyline={"category": "Technology"},
                    ),
                ),
                NewsItem(
                    id="news2",
                    content=NewsContent(
                        id="content2",
                        content_type="NEWS",
                        title="Apple stock reaches new high",
                        description=(
                            "Apple's stock price has reached a new all-time high"
                        ),
                        summary="Stock price milestone",
                        pub_date=datetime.now(),
                        display_time="2024-03-20T11:00:00Z",
                        is_hosted=False,
                        bypass_modal=False,
                        preview_url="https://example.com/preview2",
                        thumbnail=NewsThumbnail(
                            original_url="https://example.com/image2.jpg",
                            original_width=800,
                            original_height=600,
                            caption="Stock chart",
                            resolutions=[
                                NewsThumbnailResolution(
                                    url="https://example.com/image2_small.jpg",
                                    width=400,
                                    height=300,
                                    tag="small",
                                )
                            ],
                        ),
                        provider=NewsProvider(
                            display_name="Bloomberg", url="https://bloomberg.com"
                        ),
                        canonical_url=NewsUrl(
                            url="https://bloomberg.com/apple-news",
                            site="bloomberg.com",
                            region="US",
                            lang="en",
                        ),
                        click_through_url=NewsUrl(
                            url="https://bloomberg.com/apple-news",
                            site="bloomberg.com",
                            region="US",
                            lang="en",
                        ),
                        metadata=NewsMetadata(editors_pick=False),
                        finance=NewsFinance(
                            premium_finance=NewsPremiumFinance(
                                is_premium_news=True, is_premium_free_news=False
                            )
                        ),
                        storyline={"category": "Markets"},
                    ),
                ),
            ]

    return MockInstrumentsRepository()
