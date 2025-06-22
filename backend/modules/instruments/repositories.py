from datetime import datetime
from decimal import Decimal

import yfinance

from modules.instruments.exceptions import (
    FetchInstrumentInfoException,
    FetchInstrumentNewsException,
)
from modules.instruments.schemas import (
    InstrumentBasicInfoSchema,
    InstrumentDetailedInfoSchema,
    NewsItem,
)


class YFinanceRepository:
    def __init__(self, available_instruments: list[str]):
        self._available_instruments = available_instruments

    @staticmethod
    def get_instruments_info(
        tickers: list[str],
    ) -> list[InstrumentBasicInfoSchema]:
        """
        Fetches basic information for multiple instruments in a single batch request.

        Args:
            tickers (list[str]): List of ticker symbols to fetch information for.

        Returns:
            list[InstrumentBasicInfoSchema]: A list of basic instrument information.

        Raises:
            FetchInstrumentInfoException: If there's an error fetching the data.
        """
        if not tickers:
            return []

        tickers_str = " ".join(ticker.lower() for ticker in tickers)
        y_tickers = yfinance.Tickers(tickers_str)

        tickers_data = []
        tickers_errors = []

        # Use batch-fetched data from y_tickers.tickers.values()
        for ticker_obj in y_tickers.tickers.values():
            try:
                info = ticker_obj.info
                if not info:
                    tickers_errors.append(ticker_obj.ticker)
                else:
                    tickers_data.append(info)
            except Exception:
                tickers_errors.append(ticker_obj.ticker)

        if tickers_errors:
            raise FetchInstrumentInfoException(
                f"Errors fetching data: {', '.join(tickers_errors)}"
            )

        return [YFinanceRepository._get_basic_info(ticker) for ticker in tickers_data]

    @staticmethod
    def get_instrument_detailed_info(
        ticker: str,
    ) -> InstrumentDetailedInfoSchema:
        """
        Fetches detailed information for a single instrument.

        Args:
            ticker (str): The ticker symbol to fetch detailed information for.

        Returns:
            InstrumentDetailedInfoSchema: Detailed instrument information.

        Raises:
            FetchInstrumentInfoException: If there's an error fetching the data
            or if the ticker doesn't exist.
        """
        y_ticker = yfinance.Ticker(ticker)

        try:
            info = y_ticker.info
            if not info or not info.get("symbol"):
                raise FetchInstrumentInfoException(f"Invalid ticker: {ticker}")
            detailed_info = YFinanceRepository._get_detailed_info(y_ticker)
        except Exception as e:
            raise FetchInstrumentInfoException(str(e)) from e

        return detailed_info

    @staticmethod
    def _get_basic_info(ticker_info: dict) -> InstrumentBasicInfoSchema:
        ticker_symbol = ticker_info.get("symbol", "")
        basic_info = InstrumentBasicInfoSchema(
            ticker=ticker_symbol.upper(),
            name=ticker_info.get("shortName", ticker_symbol.upper()),
            currency=ticker_info.get("currency", "USD"),
            current_price=(
                Decimal(str(ticker_info["currentPrice"]))
                if ticker_info.get("currentPrice") is not None
                else None
            ),
            previous_close=(
                Decimal(str(ticker_info["previousClose"]))
                if ticker_info.get("previousClose") is not None
                else None
            ),
            market_cap=(
                Decimal(str(ticker_info["marketCap"]))
                if ticker_info.get("marketCap") is not None
                else None
            ),
            volume=ticker_info.get("volume"),
            sector=ticker_info.get("sector"),
            industry=ticker_info.get("industry"),
            country=ticker_info.get("country"),
        )

        if (
            basic_info.current_price is not None
            and basic_info.previous_close is not None
        ):
            basic_info.day_change = Decimal(str(basic_info.current_price)) - Decimal(
                str(basic_info.previous_close)
            )
            if basic_info.previous_close != Decimal(0):
                basic_info.day_change_percent = (
                    basic_info.day_change / basic_info.previous_close
                ) * 100
            elif basic_info.day_change == Decimal(0):
                basic_info.day_change_percent = Decimal(0)

        return basic_info

    @staticmethod
    def _get_detailed_info(ticker: yfinance.Ticker) -> InstrumentDetailedInfoSchema:
        ticker_info = ticker.info

        basic_schema_instance = YFinanceRepository._get_basic_info(ticker_info)

        earnings_timestamp = ticker_info.get("earningsTimestamp")
        earnings_date_value = (
            datetime.fromtimestamp(earnings_timestamp) if earnings_timestamp else None
        )

        detailed_ticker_info = InstrumentDetailedInfoSchema(
            **basic_schema_instance.model_dump(),
            description=ticker_info.get("longBusinessSummary"),
            website=ticker_info.get("website"),
            logo_url=ticker_info.get("logo_url"),
            exchange=ticker_info.get("exchange"),
            fifty_two_week_low=(
                Decimal(str(ticker_info["fiftyTwoWeekLow"]))
                if ticker_info.get("fiftyTwoWeekLow") is not None
                else None
            ),
            fifty_two_week_high=(
                Decimal(str(ticker_info["fiftyTwoWeekHigh"]))
                if ticker_info.get("fiftyTwoWeekHigh") is not None
                else None
            ),
            trailing_pe=(
                Decimal(str(ticker_info["trailingPE"]))
                if ticker_info.get("trailingPE") is not None
                else None
            ),
            forward_pe=(
                Decimal(str(ticker_info["forwardPE"]))
                if ticker_info.get("forwardPE") is not None
                else None
            ),
            dividend_yield=(
                Decimal(str(ticker_info["dividendYield"]))
                if ticker_info.get("dividendYield") is not None
                else None
            ),
            earnings_date=earnings_date_value,
        )
        major_holders = ticker.major_holders
        if major_holders is not None and not major_holders.empty:
            detailed_ticker_info.major_holders = major_holders.to_dict()

        institutional_holders = ticker.institutional_holders
        if institutional_holders is not None and not institutional_holders.empty:
            detailed_ticker_info.institutional_holders = institutional_holders.to_dict(
                "records"
            )

        recommendations = ticker.recommendations
        if recommendations is not None and not recommendations.empty:
            detailed_ticker_info.analyst_recommendations = recommendations.to_dict(
                "records"
            )

        return detailed_ticker_info

    def get_instruments_available(self) -> list[str]:
        """
        Retrieves a list of available instruments (top S&P50 for 10/6/25).

        Returns:
            list[str]: List of available instrument tickers.
        """
        return self._available_instruments

    def get_news(self, ticker_str: str) -> list[NewsItem]:
        ticker = yfinance.Ticker(ticker_str)

        try:
            news_items = [NewsItem(**item) for item in ticker.news]
        except Exception as e:
            raise FetchInstrumentNewsException(str(e)) from e

        return news_items
