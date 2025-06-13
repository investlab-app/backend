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
        self,
        instrument: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> PriceHistoryWithStats:
        """Retrieves historical price data for a given instrument.

        Retrieves price data with min and max price over the specified range.

        Args:
        ----
            instrument (str): The ticker symbol of the instrument (e.g., "AAPL").
            start_date (datetime): The starting datetime for the price data range.
            end_date (datetime): The ending datetime for the price data range.
            interval (str): The desired data interval (e.g., "1d", "1h").

        Returns:
        -------
            PriceRangeWithStats: dict with 'data' - list[InstrumentPriceSchema],
                'min_price', and 'max_price'

        Raises:
        ------
            ValidationError: If the start_date is after the end_date.
            APIException: If an error occurs while fetching data from the repository.

        """
        if start_date > end_date:
            raise InvalidTimeIntervalException(
                "Invalid date order, end date cannot preceed start date.",
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
        self._instruments: set[str] = set()
        self._subscriptions: dict[str, int] = {}
        self._clients: dict[uuid.UUID, ClientInfo] = {}

    def get_instruments(self) -> set[str]:
        return self._instruments.copy()

    def get_subscriptions(self) -> dict[str, int]:
        return self._subscriptions.copy()

    def get_clients(self) -> dict[uuid.UUID, ClientInfo]:
        return self._clients.copy()

    def subscribe(
        self,
        client_id: uuid.UUID,
        symbols: set[str],
        handler: PriceUpdateHandler | None = None,
    ) -> None:
        logging.debug(f"Subscribing client {client_id} to symbols: {symbols}")

        for symbol in iter(symbols):
            self._subscriptions.setdefault(symbol, 0)
            self._subscriptions[symbol] += 1

        client_info = self._clients.get(client_id, ClientInfo.empty())

        self._clients.update(
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
        logging.debug(f"Unsubscribing client {client_id} with symbols: {symbols}")

        instruments = (
            symbols
            if symbols
            else self._clients.get(client_id, ClientInfo.empty()).instruments
        )

        for instrument in iter(instruments):
            if instrument not in self._subscriptions:
                continue
            if self._subscriptions[instrument] > 1:
                self._subscriptions[instrument] -= 1
            else:
                del self._subscriptions[instrument]
                self._remove_instruments({instrument})

        client_symbols = self._clients.get(client_id, ClientInfo.empty()).instruments

        if symbols is None:
            # If symbols is None, remove all subscriptions for this client
            self._clients.pop(client_id, None)
        else:
            # Otherwise, remove only the specified symbols
            remaining = client_symbols - symbols
            if remaining:
                self._clients[client_id].instruments = remaining
            else:
                self._clients.pop(client_id, None)

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
        with self._lock:
            logging.debug(f"Adding instruments: {instruments}")
            self._instruments.update(instruments)

            if not self._running and self._instruments:
                self._schedule_coroutine(self._start_fetching())

    def _remove_instruments(self, instruments: set[str]) -> None:
        with self._lock:
            logging.debug(f"Removing instruments: {instruments}")
            self._instruments.difference_update(instruments)

            if not self._instruments and self._running:
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
            for client in self._clients.values()
            if (handler := client.handler)
            and client.instruments
            and prices["id"] in client.instruments
        ]

        print(handlers)

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
                # Get a copy of instruments while holding the lock
                with self._lock:
                    instruments_to_subscribe = list(self._instruments)
                await ws.subscribe(instruments_to_subscribe)
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
