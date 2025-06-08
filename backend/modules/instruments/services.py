from typing import TypedDict

from modules.instruments.repositories import YfinanceRepository
from modules.instruments.schemas import (
    InstrumentBasicInfoSchema,
    InstrumentDetailedInfoSchema,
)
from modules.prices.constants import YFinanceTimeInterval
from modules.prices.exceptions import InvalidTimeIntervalException


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
            PaginatedInstruments: Paginated list of instruments with total count and page info
        """
        instruments = self._repository.get_instruments_info(tickers)

        if filter_sector:
            instruments = [i for i in instruments if i.sector == filter_sector]

        if filter_industry:
            instruments = [i for i in instruments if i.industry == filter_industry]

        if sort_by and sort_by in InstrumentBasicInfoSchema.model_fields:
            reverse = sort_direction.lower() == "desc"
            instruments.sort(
                key=lambda x: (
                    getattr(x, sort_by)
                    if getattr(x, sort_by) is not None
                    else (0 if reverse else float("inf"))
                ),
                reverse=reverse,
            )

        total_items = len(instruments)
        total_pages = (
            (total_items + page_size - 1) // page_size if total_items > 0 else 1
        )

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
