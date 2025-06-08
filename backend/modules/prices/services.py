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
        Retrieves historical price data for an instrument, including minimum and maximum prices.
        
        Fetches price history for the specified instrument and date range at the given interval, returning the data along with the lowest and highest prices observed.
        
        Args:
            instrument: The ticker symbol of the instrument.
            start_date: The start of the date range for price data.
            end_date: The end of the date range for price data.
            interval: The interval between data points (e.g., "1d", "1h").
        
        Returns:
            A dictionary containing the price data list, minimum price, and maximum price.
        
        Raises:
            InvalidTimeIntervalException: If start_date is after end_date.
            ValidationError: If input validation fails.
            APIException: If an error occurs while fetching data.
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
        """
        Initializes the LivePrices service, setting up handler and instrument storage and starting the background event loop in a separate thread.
        """
        self.handlers: list[PriceUpdateHandler] = []
        self.instruments: set[str] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False
        self._lock = threading.Lock()
        self._start_background_loop()

    def _start_background_loop(self) -> None:
        """
        Starts a background thread running an asyncio event loop for asynchronous tasks.
        
        Initializes a new asyncio event loop in a dedicated daemon thread and sets it as the current event loop for that thread. This enables scheduling and execution of asynchronous operations in the background.
        """
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()

        logging.debug("Starting background event loop")

        loop_thread = threading.Thread(target=run_loop, daemon=True)
        loop_thread.start()

        time.sleep(0.1)

    def _schedule_coroutine(self, coro):
        """
        Schedules a coroutine to run on the background event loop.
        
        If the event loop is active, submits the coroutine for execution in a thread-safe manner. Returns a Future representing the execution, or None if the event loop is unavailable.
        
        Args:
            coro: The coroutine to schedule.
        
        Returns:
            A concurrent.futures.Future if scheduled, or None if the event loop is not running.
        """
        logging.debug(f"Scheduling coroutine: {coro}")

        if self._loop and not self._loop.is_closed():
            return asyncio.run_coroutine_threadsafe(coro, self._loop)
        return None

    def add_instruments(self, instruments: set[str]) -> None:
        """
        Adds instruments to the set being tracked for live price updates.
        
        If new instruments are added and there are registered handlers, starts the live price fetching loop.
        """
        with self._lock:
            logging.debug(f"Adding instruments: {instruments}")
            self.instruments.update(instruments)

            # If we added new instruments and we're not running, start
            if not self._running and self.instruments and self.handlers:
                self._schedule_coroutine(self._start_fetching())

    def remove_instruments(self, instruments: set[str]) -> None:
        """
        Removes specified instruments from the set being tracked.
        
        If no instruments remain after removal and live fetching is active, stops the fetching loop.
        """
        with self._lock:
            logging.debug(f"Removing instruments: {instruments}")
            self.instruments.difference_update(instruments)

            if not self.instruments and self._running:
                self._schedule_coroutine(self._stop_fetching())

    def add_handler(self, handler: PriceUpdateHandler) -> None:
        """
        Registers a handler to receive live price updates.
        
        If this is the first handler and there are tracked instruments, starts the live price fetching loop.
        """
        with self._lock:
            logging.debug(f"Adding handler: {handler}")
            self.handlers.append(handler)

            if not self._running and self.instruments and len(self.handlers) == 1:
                self._schedule_coroutine(self._start_fetching())

    def remove_handler(self, handler: PriceUpdateHandler) -> None:
        """
        Removes a registered price update handler.
        
        If this is the last handler and live price updates are running, stops the fetching loop.
        """
        with self._lock:
            logging.debug(f"Removing handler: {handler}")
            if handler in self.handlers:
                self.handlers.remove(handler)

                if not self.handlers and self._running:
                    self._schedule_coroutine(self._stop_fetching())

    async def _start_fetching(self):
        """
        Starts the live price fetching loop if it is not already running.
        
        This method sets the running flag and schedules the asynchronous fetch loop to begin dispatching live price updates to registered handlers.
        """
        if self._running:
            return
        self._running = True
        asyncio.create_task(self._fetch_loop())
        logging.info("Starting live price fetching loop")

    async def _stop_fetching(self):
        """
        Stops the live price fetching loop asynchronously by setting the running flag to False.
        """
        self._running = False
        logging.info("Stopping live price fetching loop")

    async def _fetch_loop(self):
        """
        Continuously generates and dispatches simulated price updates to all registered handlers.
        
        While the service is running and both instruments and handlers are present, this loop generates random price data for each instrument every second and invokes all registered handlers with the price updates. Supports both synchronous and asynchronous handlers. Errors during handler invocation or price generation are logged, and the loop continues operation unless explicitly stopped.
        """
        while self._running and self.instruments and self.handlers:
            try:
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
        """
        Stops the live price update service and shuts down the background event loop.
        
        This method halts price fetching, prevents further handler notifications, and cleanly stops the background asyncio event loop.
        """
        with self._lock:
            logging.info("Shutting down LivePrices service")
            self._running = False
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
