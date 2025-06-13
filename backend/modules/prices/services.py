import asyncio
import threading
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TypedDict

import yfinance

from config import parse_time_interval
from config.logging import get_logger
from modules.prices.exceptions import InvalidTimeIntervalException
from modules.prices.repositories import YfinanceRepository
from modules.prices.schemas import ClientInfo, InstrumentPriceSchema, PriceUpdateHandler

logger = get_logger(__name__)


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

    def set_client(self, uuid: uuid.UUID, client: ClientInfo) -> None:
        self._clients[uuid] = client

    def get_instruments(self) -> set[str]:
        return self._instruments.copy()

    def get_subscriptions(self) -> dict[str, int]:
        return self._subscriptions.copy()

    def get_clients(self) -> dict[uuid.UUID, ClientInfo]:
        return self._clients.copy()

    def subscribe(
        self, client_id: uuid.UUID, symbols: set[str] | None = None,
        handler: PriceUpdateHandler | None = None,
    ) -> None:
        logger.debug("Subscribing client %s to symbols: %s", client_id, symbols)

        for symbol in iter(symbols):
            self._add_instruments({symbol})

        client_info = self._clients.get(client_id, ClientInfo.empty())

        self._clients.update(
            {
                client_id: ClientInfo(
                    instruments=client_info.instruments | symbols,
                    handler=handler if handler else client_info.handler,
                )
            }
        )

    def unsubscribe(
        self, client_id: uuid.UUID, symbols: set[str] | None = None
    ) -> None:
        logger.debug("Unsubscribing client %s with symbols: %s", client_id, symbols)

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

        logger.debug("Starting background event loop")

        loop_thread = threading.Thread(target=run_loop, daemon=True)
        loop_thread.start()

        time.sleep(0.1)

    def _schedule_coroutine(self, coro):
        logger.debug("Scheduling coroutine: %s", coro)

        if self._loop and not self._loop.is_closed():
            return asyncio.run_coroutine_threadsafe(coro, self._loop)

        return None

    def _add_instruments(self, instruments: set[str]) -> None:
        with self._lock:
            logger.debug("Adding instruments: %s", instruments)
            self._instruments.update(instruments)

            if not self._running and self._instruments:
                self._schedule_coroutine(self._start_fetching())

    def _remove_instruments(self, instruments: set[str]) -> None:
        with self._lock:
            logger.debug("Removing instruments: %s", instruments)
            self._instruments.difference_update(instruments)

            if not self._instruments and self._running:
                self._schedule_coroutine(self._stop_fetching())

    async def _start_fetching(self):
        if self._running:
            return

        logger.debug("Starting live price fetching")

        asyncio.create_task(self._fetch_loop())

    async def _stop_fetching(self):
        logger.debug("Stopping live price fetching loop")
        self._running = False

    def message_handler(self, prices):
        logger.debug("Handling price update: %s", prices)

        handlers = [
            client.handler
            for client in self._clients.values()
            if client.handler is not None
        ]

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    if self._loop and not self._loop.is_closed():
                        asyncio.run_coroutine_threadsafe(handler(prices), self._loop)
                    else:
                        logger.error("Event loop not available for async handler")
                else:
                    handler(prices)
            except Exception as e:
                logger.error("Error in handler %s: %s", handler, e)

    async def _fetch_loop(self):
        logger.debug("Starting fetch loop")
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
            logger.error("Error in fetch loop: %s", e)
        finally:
            self._running = False

    def shutdown(self):
        """Shutdown the service"""
        with self._lock:
            logger.debug("Starting shutdown process")
            self._running = False
            if self._loop and not self._loop.is_closed():
                self._loop.call_soon_threadsafe(self._loop.stop)
