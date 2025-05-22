from datetime import datetime
from decimal import Decimal

from yfinance import Ticker, Tickers

from modules.instruments.exceptions import FetchInstrumentInfoException
from modules.instruments.schemas import (
    InstrumentBasicInfoSchema,
    InstrumentDetailedInfoSchema,
)


class YfinanceRepository:
    @staticmethod
    def get_instruments_info(
        tickers: list[str],
    ) -> list[InstrumentBasicInfoSchema]:
        """
        Fetches basic information for multiple instruments.

        Args:
            tickers (list[str]): List of ticker symbols to fetch information for.

        Returns:
            list[InstrumentBasicInfoSchema]: A list of basic instrument information.

        Raises:
            FetchInstrumentInfoException: If there's an error fetching the data.
        """
        tickers_str = " ".join(ticker.lower() for ticker in tickers)
        y_tickers = Tickers(tickers_str)

        try:
            tickers_data = [
                y_tickers.tickers[ticker.upper()].info for ticker in tickers
            ]
        except Exception as e:
            raise FetchInstrumentInfoException(str(e)) from e

        return [YfinanceRepository._get_basic_info(ticker) for ticker in tickers_data]

    @staticmethod
    def get_instrument_detailed_info(
        ticker_str: str,
    ) -> InstrumentDetailedInfoSchema:
        """
        Fetches detailed information for a single instrument.

        Args:
            ticker (str): The ticker symbol to fetch detailed information for.

        Returns:
            InstrumentDetailedInfoSchema: Detailed instrument information.

        Raises:
            FetchInstrumentInfoException: If there's an error fetching the data or if the ticker doesn't exist.
        """
        ticker = Ticker(ticker_str)

        try:
            detailed_info = YfinanceRepository._get_detailed_info(ticker)
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
                Decimal(str(ticker_info.get("currentPrice", 0)))
                if ticker_info.get("currentPrice") is not None
                else None
            ),
            previous_close=(
                Decimal(str(ticker_info.get("previousClose", 0)))
                if ticker_info.get("previousClose") is not None
                else None
            ),
            market_cap=(
                Decimal(str(ticker_info.get("marketCap", 0)))
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
            basic_info.day_change = basic_info.current_price - basic_info.previous_close
            if basic_info.previous_close != Decimal(0):
                basic_info.day_change_percent = (
                    basic_info.day_change / basic_info.previous_close
                ) * 100
            elif basic_info.day_change == Decimal(0):
                basic_info.day_change_percent = Decimal(0)

        return basic_info

    @staticmethod
    def _get_detailed_info(ticker: Ticker) -> InstrumentDetailedInfoSchema:
        ticker_info = ticker.info

        basic_schema_instance = YfinanceRepository._get_basic_info(ticker_info)

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
                Decimal(str(ticker_info.get("fiftyTwoWeekLow", 0)))
                if ticker_info.get("fiftyTwoWeekLow") is not None
                else None
            ),
            fifty_two_week_high=(
                Decimal(str(ticker_info.get("fiftyTwoWeekHigh", 0)))
                if ticker_info.get("fiftyTwoWeekHigh") is not None
                else None
            ),
            trailing_pe=(
                Decimal(str(ticker_info.get("trailingPE", 0)))
                if ticker_info.get("trailingPE") is not None
                else None
            ),
            forward_pe=(
                Decimal(str(ticker_info.get("forwardPE", 0)))
                if ticker_info.get("forwardPE") is not None
                else None
            ),
            dividend_yield=(
                Decimal(str(ticker_info.get("dividendYield", 0)))
                if ticker_info.get("dividendYield") is not None
                else None
            ),
            earnings_date=earnings_date_value,
            business_summary=ticker_info.get("longBusinessSummary"),
        )
        major_holders = ticker.major_holders
        if not major_holders.empty:
            detailed_ticker_info.major_holders = major_holders.to_dict()

        institutional_holders = ticker.institutional_holders
        if not institutional_holders.empty:
            detailed_ticker_info.institutional_holders = institutional_holders.to_dict(
                "records"
            )

        recommendations = ticker.recommendations
        if not recommendations.empty:
            detailed_ticker_info.analyst_recommendations = recommendations.to_dict(
                "records"
            )

        return detailed_ticker_info
