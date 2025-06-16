from typing import TypedDict

from modules.instruments.repositories import YfinanceRepository
from modules.instruments.schemas import (
    InstrumentBasicInfoSchema,
    InstrumentDetailedInfoSchema,
    NewsItem,
)


class PaginatedInstruments(TypedDict):
    items: list[InstrumentBasicInfoSchema]
    total: int
    page: int
    page_size: int
    num_pages: int


class InstrumentsServiceMinimal:
    def __init__(self):
        self._repository = YfinanceRepository()

    def get_instruments_list(
        self,
        tickers: list[str],
        page: int = 1,
        page_size: int = 10,
        sort_by: str | None = None,
        sort_direction: str = "asc",
        filter_sector: str | None = None,
        filter_industry: str | None = None,
    ) -> PaginatedInstruments:
        """
        Retrieves a paginated, sorted, and filtered list of instruments.

        Args:
            tickers: List of ticker symbols to retrieve information for
            page: Current page number (1-indexed)
            page_size: Number of items per page
            sort_by: Field to sort by (e.g., 'market_cap', 'current_price')
            sort_direction: 'asc' or 'desc'
            filter_sector: Filter by sector name
            filter_industry: Filter by industry name

        Returns:
            PaginatedInstruments: Paginated list of instruments with total count and
            page info.
        """
        instruments = self._repository.get_instruments_info(tickers)

        if filter_sector:
            instruments = [i for i in instruments if i.sector == filter_sector]

        if filter_industry:
            instruments = [i for i in instruments if i.industry == filter_industry]

        if sort_by and hasattr(InstrumentBasicInfoSchema, sort_by):
            assert isinstance(sort_by, str)
            reverse = sort_direction.lower() == "desc"
            default_sort_value = float("-inf") if reverse else float("inf")
            instruments.sort(
                key=lambda x, key=sort_by: getattr(x, key, default_sort_value),
                reverse=reverse,
            )

        total_items = len(instruments)
        page_size = max(1, page_size)
        total_pages = (total_items + page_size - 1) // page_size

        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        page_items = instruments[start_idx:end_idx]

        return PaginatedInstruments(
            items=page_items,
            total=total_items,
            page=page,
            page_size=page_size,
            num_pages=total_pages,
        )

    def get_instrument_detailed_info(self, ticker: str) -> InstrumentDetailedInfoSchema:
        """
        Retrieves detailed information for a single instrument.

        Args:
            ticker: Ticker symbol to retrieve information for

        Returns:
            InstrumentDetailedInfoSchema: Detailed instrument information
        """
        return self._repository.get_instrument_detailed_info(ticker)

    def get_instruments_available(self) -> list[str]:
        """
        Retrieves a list of available instruments (top S&P50 for 10/6/25).

        Returns:
            list[str]: List of available instrument tickers.
        """
        return self._repository.get_instruments_available()

    def get_news(self, ticker: str) -> list[NewsItem]:
        """
        Retrieves news for a single instrument.

        Args:
            ticker: Ticker symbol to retrieve news for

        Returns:
            list[NewsItem]: List of news items
        """
        return self._repository.get_news(ticker)
