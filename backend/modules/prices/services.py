import asyncio
import logging
import random
import threading
import time
from datetime import datetime
from decimal import Decimal
from typing import Callable, TypedDict

from config import parse_time_interval
from modules.prices.exceptions import InvalidTimeIntervalException
from modules.prices.repositories import YfinanceRepository
from modules.prices.schemas import InstrumentPriceSchema


class PriceHistoryWithStats(TypedDict):
    data: list[InstrumentPriceSchema]
    min_price: Decimal
    max_price: Decimal


class PricesServiceMinimal:
    def __init__(self):
        self._repository = YfinanceRepository()

    def get_instrument_price_history(
        self, instrument: str, start_date: datetime, end_date: datetime, interval: str
    ) -> PriceHistoryWithStats:
        """
        Retrieves historical price data for a given instrument with min and max price over the range.

        Args:
            instrument (str): The ticker symbol of the instrument (e.g., "AAPL").
            start_date (datetime): The starting datetime for the price data range.
            end_date (datetime): The ending datetime for the price data range.
            interval (str): The desired data interval (e.g., "1d", "1h").

        Returns:
            PriceRangeWithStats: dict with 'data' - list[InstrumentPriceSchema], 'min_price', and 'max_price'

        Raises:
            ValidationError: If the start_date is after the end_date.
            APIException: If an error occurs while fetching data from the repository.
        """

        if start_date > end_date:
            raise InvalidTimeIntervalException(
                "Invalid date order, end date cannot preceed start date."
            )
        data = self._repository.get_instrument_price_history(
            instrument,
            start_date,
            end_date,
            parse_time_interval(interval.lower()),
        )
        min_price = min(d.low for d in data)
        max_price = max(d.high for d in data)

        return PriceHistoryWithStats(
            data=data, min_price=min_price, max_price=max_price
        )


type PriceUpdateHandler = Callable[[dict[str, float]], None]


class LivePrices:

    def __init__(self) -> None:
        self.handlers: list[PriceUpdateHandler] = []
        self.instruments: set[str] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False
        self._lock = threading.Lock()
        self._start_background_loop()

    def _start_background_loop(self) -> None:
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        logging.debug("Starting background event loop")

        loop_thread = threading.Thread(target=run_loop, daemon=True)
        loop_thread.start()

        time.sleep(0.1)

    def _schedule_coroutine(self, coro):
        logging.debug(f"Scheduling coroutine: {coro}")

        if self._loop and not self._loop.is_closed():
            return asyncio.run_coroutine_threadsafe(coro, self._loop)
        return None

    def add_instruments(self, instruments: set[str]) -> None:
        """Add instruments to track"""
        with self._lock:
            logging.debug(f"Adding instruments: {instruments}")
            self.instruments.update(instruments)

            # If we added new instruments and we're not running, start
            if not self._running and self.instruments and self.handlers:
                self._schedule_coroutine(self._start_fetching())

    def remove_instruments(self, instruments: set[str]) -> None:
        """Remove instruments (sync method)"""
        with self._lock:
            logging.debug(f"Removing instruments: {instruments}")
            self.instruments.difference_update(instruments)

            if not self.instruments and self._running:
                self._schedule_coroutine(self._stop_fetching())

    def add_handler(self, handler: PriceUpdateHandler) -> None:
        """Add price update handler (sync method)"""
        with self._lock:
            logging.debug(f"Adding handler: {handler}")
            self.handlers.append(handler)

            if not self._running and self.instruments and len(self.handlers) == 1:
                self._schedule_coroutine(self._start_fetching())

    def remove_handler(self, handler: PriceUpdateHandler) -> None:
        """Remove price update handler (sync method)"""
        with self._lock:
            logging.debug(f"Removing handler: {handler}")
            if handler in self.handlers:
                self.handlers.remove(handler)

                if not self.handlers and self._running:
                    self._schedule_coroutine(self._stop_fetching())

    async def _start_fetching(self):
        if self._running:
            return
        self._running = True
        asyncio.create_task(self._fetch_loop())
        logging.info("Starting live price fetching loop")

    async def _stop_fetching(self):
        self._running = False
        logging.info("Stopping live price fetching loop")

    async def _fetch_loop(self):
        while self._running and self.instruments and self.handlers:
            try:
                print(f"Fetching live prices for: {self.instruments}")

                prices = {
                    instrument: random.uniform(100, 500)
                    for instrument in self.instruments
                }

                handler_tasks = []
                for handler in self.handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            handler_tasks.append(handler(prices))
                        else:
                            handler_tasks.append(
                                asyncio.get_event_loop().run_in_executor(
                                    None, handler, prices
                                )
                            )
                    except Exception as e:
                        logging.error(f"Error preparing handler call: {e}")

                if handler_tasks:
                    await asyncio.gather(*handler_tasks, return_exceptions=True)

                await asyncio.sleep(1)

            except Exception as e:
                logging.error(f"Error in fetch loop: {e}")
                await asyncio.sleep(1)

        self._running = False

    def shutdown(self):
        """Shutdown the service"""
        with self._lock:
            logging.info("Shutting down LivePrices service")
            self._running = False
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
