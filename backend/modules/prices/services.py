import asyncio
import logging
import threading
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Callable, TypedDict

import yfinance
from pydantic import BaseModel

from config import parse_time_interval
from modules.prices.exceptions import InvalidTimeIntervalException
from modules.prices.repositories import YfinanceRepository
from modules.prices.schemas import ClientInfo, InstrumentPriceSchema, PriceUpdateHandler


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


class LivePrices:

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._running = False
        self._lock = threading.Lock()
        self._start_background_loop()
        self.instruments: set[str] = set()
        self.subscriptions: dict[str, int] = {}
        self.clients: dict[uuid.UUID, ClientInfo] = {}

    def subscribe(
        self,
        client_id: uuid.UUID,
        symbols: set[str],
        handler: PriceUpdateHandler | None = None,
    ) -> None:
        with self._lock:
            logging.debug(f"Subscribing client {client_id} to symbols: {symbols}")

            for symbol in iter(symbols):
                self.subscriptions.setdefault(symbol, 0)
                self.subscriptions[symbol] += 1

            client_info = self.clients.get(client_id, ClientInfo.empty())

            self.clients.update(
                {
                    client_id: ClientInfo(
                        instruments=client_info.instruments | symbols,
                        handler=handler if handler else client_info.handler,
                    )
                }
            )

            self._add_instruments(symbols)

    def unsubscribe(
        self, client_id: uuid.UUID, symbols: set[str] | None = None
    ) -> None:
        with self._lock:
            logging.debug(f"Unsubscribing client {client_id} with symbols: {symbols}")

            if not symbols:
                symbols = self.clients.get(client_id, ClientInfo.empty()).instruments

            for symbol in iter(symbols):
                if symbol not in self.subscriptions:
                    continue
                if self.subscriptions[symbol] > 1:
                    self.subscriptions[symbol] -= 1
                else:
                    del self.subscriptions[symbol]
                    self._remove_instruments({symbol})

            client_symbols = self.clients.get(client_id, ClientInfo.empty()).instruments

            remaining = client_symbols - symbols
            if remaining:
                self.clients[client_id].instruments = remaining
            else:
                self.clients.pop(client_id, None)

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

    def _add_instruments(self, instruments: set[str]) -> None:
        logging.debug(f"Adding instruments: {instruments}")
        self.instruments.update(self.instruments | instruments)

        if not self._running and self.instruments:
            print(f"Starting live price fetching for instruments: {self.instruments}")
            self._schedule_coroutine(self._start_fetching())

    def _remove_instruments(self, instruments: set[str]) -> None:
        logging.debug(f"Removing instruments: {instruments}")
        self.instruments.difference_update(instruments)

        if not self.instruments and self._running:
            self._schedule_coroutine(self._stop_fetching())

    async def _start_fetching(self):
        if self._running:
            return

        logging.debug("Starting live price fetching")

        asyncio.create_task(self._fetch_loop())

    async def _stop_fetching(self):
        logging.debug("Stopping live price fetching loop")
        self._running = False

    def message_handler(self, prices):
        logging.debug(f"Handling price update: {prices}")

        handlers = [
            handler
            for client in self.clients.values()
            if (handler := client.handler) is not None
        ]

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    if self._loop and not self._loop.is_closed():
                        asyncio.run_coroutine_threadsafe(handler(prices), self._loop)
                    else:
                        logging.error("Event loop not available for async handler")
                else:
                    handler(prices)
            except Exception as e:
                logging.error(f"Error in handler {handler}: {e}")

    async def _fetch_loop(self):
        logging.debug("Starting fetch loop")
        if self._running:
            return

        self._running = True

        try:
            async with yfinance.AsyncWebSocket() as ws:
                await ws.subscribe(list(self.instruments))
                await ws.listen(self.message_handler)
        except Exception as e:
            logging.error(f"Error in fetch loop: {e}")
        finally:
            self._running = False

    def shutdown(self):
        """Shutdown the service"""
        with self._lock:
            logging.debug("Starting shutdown process")
            self._running = False
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
