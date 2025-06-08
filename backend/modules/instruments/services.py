from typing import TypedDict

from modules.instruments.repositories import YfinanceRepository
from modules.instruments.schemas import (
    InstrumentBasicInfoSchema,
    InstrumentDetailedInfoSchema,
)


class PaginatedInstruments(TypedDict):
    items: list[InstrumentBasicInfoSchema]
    total: int
    page: int
    page_size: int
    num_pages: int


class InstrumentsServiceMinimal:
    def __init__(self):
        """
        Initializes the InstrumentsServiceMinimal with a YfinanceRepository instance.
        """
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
        Retrieves a paginated list of instruments with optional sorting and filtering.
        
        Filters instruments by sector and industry if specified, sorts by a given attribute in ascending or descending order, and returns the specified page of results along with pagination metadata.
        
        Args:
            tickers: List of ticker symbols to retrieve instrument information for.
            page: Page number to return (1-indexed).
            page_size: Number of items per page.
            sort_by: Attribute to sort by (e.g., 'market_cap', 'current_price').
            sort_direction: Sort order, either 'asc' for ascending or 'desc' for descending.
            filter_sector: Sector name to filter instruments by.
            filter_industry: Industry name to filter instruments by.
        
        Returns:
            A PaginatedInstruments dictionary containing the paginated list of instruments and pagination details.
        """
        instruments = self._repository.get_instruments_info(tickers)

        if filter_sector:
            instruments = [i for i in instruments if i.sector == filter_sector]

        if filter_industry:
            instruments = [i for i in instruments if i.industry == filter_industry]

        if sort_by and hasattr(InstrumentBasicInfoSchema, sort_by):
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
        Retrieves detailed information for a financial instrument by its ticker symbol.
        
        Args:
            ticker: The ticker symbol identifying the instrument.
        
        Returns:
            An object containing comprehensive details about the specified instrument.
        """
        return self._repository.get_instrument_detailed_info(ticker)
