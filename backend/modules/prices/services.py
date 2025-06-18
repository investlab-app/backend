import asyncio
import threading
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TypedDict

import yfinance

from config.logging import get_logger
from config.utils import parse_time_interval
from modules.prices.exceptions import InvalidTimeIntervalException
from modules.prices.repositories import YfinanceRepository
from modules.prices.schemas import ClientInfo, InstrumentPriceSchema, PriceUpdateHandler

logger = get_logger(__name__)


class PriceHistoryWithStats(TypedDict):
    data: list[InstrumentPriceSchema]
    min_price: Decimal
    max_price: Decimal


class PricesService:
    def __init__(self, repository: YfinanceRepository):
        self._repository = repository

    def get_instrument_price_history(
        self,
        instrument: str,
        start_date: datetime,
        end_date: datetime,
        interval: str,
    ) -> PriceHistoryWithStats:
        """
        Retrieves historical price data for a given instrument.

        Retrieves price data with min and max price over the specified range.

        Args:
            instrument (str): The ticker symbol of the instrument (e.g., "AAPL").
            start_date (datetime): The starting datetime for the price data range.
            end_date (datetime): The ending datetime for the price data range.
            interval (str): The desired data interval (e.g., "1d", "1h").

        Returns:
            PriceRangeWithStats: dict with 'data' - list[InstrumentPriceSchema],
                'min_price', and 'max_price'

        Raises:
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
        logger.debug("Got data: %s", data)
        min_price = min(d.low for d in data)
        max_price = max(d.high for d in data)

        return PriceHistoryWithStats(
            data=data, min_price=min_price, max_price=max_price
        )


class LivePricesService:
    def __init__(self) -> None:
        self._instruments: set[str] = set()
        self._subscriptions: dict[str, int] = {}
        self._clients: dict[uuid.UUID, ClientInfo] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None

    def _restart_task(self):
        if not self._loop:
            logger.debug("Creating new event loop")
            self._loop = asyncio.new_event_loop()
            prices_thread = threading.Thread(target=self._loop.run_forever, daemon=True)
            prices_thread.start()

        def _create_task():
            if self._task and not self._task.done():
                logger.debug("Cancelling existing task")
                self._task.cancel()

            logger.debug("Creating new task")
            self._task = self._loop.create_task(self._fetch_loop())

        # Schedule the task creation in the event loop thread
        self._loop.call_soon_threadsafe(_create_task)

    async def _fetch_loop(self):
        logger.debug("Starting fetch loop")

        try:
            async with yfinance.AsyncWebSocket() as ws:
                instruments_to_subscribe = list(self._instruments)
                logger.debug("Subscribing to instruments: %s", instruments_to_subscribe)
                await ws.subscribe(instruments_to_subscribe)
                await ws.listen(self.message_handler)
        except Exception as e:
            logger.error("Error in fetch loop: %s", e)

    def message_handler(self, prices):
        logger.debug("Handling price update: %s", prices)

        handlers = [
            handler
            for client in self._clients.values()
            if (handler := client.handler)
            and client.instruments
            and prices["id"] in client.instruments
        ]

        for handler in handlers:
            handler(prices)

    def subscribe(
        self,
        client_id: uuid.UUID,
        symbols: set[str],
        handler: PriceUpdateHandler | None = None,
    ) -> None:
        logger.debug("Subscribing client %s to symbols: %s", client_id, symbols)

        for symbol in symbols:
            if (
                symbol
                not in self._clients.get(client_id, ClientInfo.empty()).instruments
            ):
                logger.debug("Adding instrument: %s", symbol)
                self._instruments.add(symbol)
                self._subscriptions[symbol] = self._subscriptions.get(symbol, 0) + 1
                self._restart_task()

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

        logger.info("SUBSCRIPTIONS: %s", self._subscriptions)

        for instrument in iter(instruments):
            if instrument not in self._subscriptions:
                continue
            if self._subscriptions[instrument] > 1:
                self._subscriptions[instrument] -= 1
            else:
                logger.debug("Removing instrument: %s", instrument)
                del self._subscriptions[instrument]
                self._instruments.remove(instrument)
                self._restart_task()

        client_symbols = self._clients.get(client_id, ClientInfo.empty()).instruments

        if symbols is None:
            self._clients.pop(client_id, None)
        else:
            remaining = client_symbols - symbols
            if remaining:
                self._clients[client_id].instruments = remaining
            else:
                self._clients.pop(client_id, None)
