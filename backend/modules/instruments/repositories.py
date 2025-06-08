from datetime import datetime
from decimal import Decimal

import yfinance

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
        Retrieves basic information for a list of financial instruments by their ticker symbols.
        
        Returns a list of InstrumentBasicInfoSchema objects containing summary data for each requested ticker. Raises FetchInstrumentInfoException if data retrieval fails.
        """
        tickers_str = " ".join(ticker.lower() for ticker in tickers)
        y_tickers = yfinance.Tickers(tickers_str)

        try:
            tickers_data = [
                y_tickers.tickers[ticker.upper()].info for ticker in tickers
            ]
        except Exception as e:
            raise FetchInstrumentInfoException(str(e)) from e

        return [YfinanceRepository._get_basic_info(ticker) for ticker in tickers_data]

    @staticmethod
    def get_instrument_detailed_info(
        ticker: str,
    ) -> InstrumentDetailedInfoSchema:
        """
        Retrieves detailed information for a financial instrument by its ticker symbol.
        
        Fetches and structures comprehensive data for the specified ticker, including business summary, financial ratios, holders, and analyst recommendations. Raises a FetchInstrumentInfoException if data retrieval or processing fails.
        
        Returns:
            An InstrumentDetailedInfoSchema containing detailed instrument data.
        
        Raises:
            FetchInstrumentInfoException: If an error occurs during data fetching or processing.
        """
        y_ticker = yfinance.Ticker(ticker)

        try:
            detailed_info = YfinanceRepository._get_detailed_info(y_ticker)
        except Exception as e:
            raise FetchInstrumentInfoException(str(e)) from e

        return detailed_info

    @staticmethod
    def _get_basic_info(ticker_info: dict) -> InstrumentBasicInfoSchema:
        """
        Converts a raw ticker information dictionary into an InstrumentBasicInfoSchema.
        
        Extracts and formats key financial fields such as symbol, name, currency, current price, previous close, market cap, volume, sector, industry, and country. Calculates day change and day change percentage if price data is available. Numeric values are converted to Decimal where applicable.
        
        Args:
            ticker_info: Dictionary containing raw ticker data from yfinance.
        
        Returns:
            An InstrumentBasicInfoSchema instance populated with the extracted and computed fields.
        """
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
    def _get_detailed_info(ticker: yfinance.Ticker) -> InstrumentDetailedInfoSchema:
        """
        Builds a detailed instrument information schema from a yfinance Ticker object.
        
        Extracts and structures both basic and extended financial data, including business summary, website, logo URL, exchange, 52-week range, P/E ratios, dividend yield, earnings date, major holders, institutional holders, and analyst recommendations.
        
        Args:
            ticker: A yfinance Ticker object containing instrument data.
        
        Returns:
            An InstrumentDetailedInfoSchema instance with comprehensive instrument details.
        """
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
