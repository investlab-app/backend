from typing import TypedDict
from django.db import transaction
import traceback
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor
import polygon
from django.db.utils import IntegrityError

from config.logging import get_logger
from config.polygon import client
from modules.instruments.repositories import YFinanceRepository
from modules.instruments.schemas import (
    InstrumentBasicInfoSchema,
    InstrumentDetailedInfoSchema,
    NewsItem,
)
from modules.instruments.models import InstrumentV2
from modules.instruments.serializers import TickerOverviewResultSerializer, TestSerializer

logger = get_logger(__name__)


class PaginatedInstruments(TypedDict):
    items: list[InstrumentBasicInfoSchema]
    total: int
    page: int
    page_size: int
    num_pages: int


class InstrumentsService:
    def __init__(self, repository: YFinanceRepository):
        self._repository = repository

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
        logger.debug(
            "Getting available instruments from repository: %s", self._repository
        )
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

class InstrumentServiceV2:
    a = 0

    @staticmethod
    def pull_instrument_details(ticker):
        InstrumentServiceV2.a += 1
        if InstrumentServiceV2.a % 50 == 0:
            print(InstrumentServiceV2.a)
        return asdict(client.get_ticker_details(ticker))

    @staticmethod
    def pull_all_instruments():
        tickers = []
        i = 0
        for t in client.list_tickers(limit=1000):
            tickers.append(t)
            i += 1
            if i % 50 == 0:
                print(i)

        names = [t.ticker for t in tickers]
        results = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            f = InstrumentServiceV2.pull_instrument_details
            results = list(executor.map(f, names))

        serializers = []
        for r in results:
            serializers.append(TickerOverviewResultSerializer(data=r))

        with transaction.atomic():
            for s in serializers:
                if s.is_valid():
                    i = s.save()
                    print(f"Saved {i.ticker}")
                else:
                    print(f'{s.initial_data["ticker"]} is invalid')
                    print(s.errors)



        


        # for t in results:
        #     print('-'*60)
        #     print(f'{t.ticker}')
        #     print('-'*60)
        #     print(t)
        #     print('\n')
        print(f'Fetched {len(results)} results')
        # a = client.get_ticker_details("AAPL")
        # s = TickerOverviewResultSerializer(data=asdict(a))
        # print(s.is_valid())
        # if s.is_valid():
        #     i = s.save()
        #     i.save()
        # print(asdict(a))
        # print(s.is_valid())
        # print(s.validated_data)

        #s = InstrumentApiSerializer(data=d)
        #print(s.is_valid())
        #s.save()

    # @staticmethod
    # def PolygonDetailToInstrument(details :polygon.rest.reference.TickerDetails):
    #     instrument = InstrumentV2()
    #     instrument.delisted = details.active
    #     if details.address:
    #         instrument.address1 = 
    #     instrument.icon_url = details.branding.icon_url
