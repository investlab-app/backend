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
from modules.prices.schemas import (
    Client,
    ClientId,
    HandlerFn,
    InstrumentPriceSchema,
    TickerId,
)

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
            data=data,
            min_price=min_price,
            max_price=max_price,
        )


class LivePricesService:
    def __init__(self) -> None:
        self._clients: dict[ClientId, Client] = {}
        self._tickers: dict[TickerId, list[ClientId]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._task: asyncio.Task | None = None
        self._lock = threading.Lock()

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
                tickers_to_subscribe = list(self._tickers.keys())
                logger.debug("Subscribing to instruments: %s", tickers_to_subscribe)
                await ws.subscribe(tickers_to_subscribe)
                await ws.listen(self.message_handler)
        except Exception as e:
            logger.error("Error in fetch loop: %s", e)

    def message_handler(self, prices):
        # logger.debug("Received message: %s", prices)

        logger.debug("clients: %s", self._clients)

        handlers = [
            handler
            for client in self._clients.values()
            if (handler := client.handler)
            and client.tickers
            and prices["id"] in client.tickers
        ]

        for handler in handlers:
            handler(prices)

    def update(
        self,
        client_id: uuid.UUID,
        tickers: set[str],
    ) -> None:
        logger.debug("Updating client %s with symbols: %s", client_id, tickers)

        client = self._clients.get(client_id)

        if not client:
            logger.debug("Client %s not found, not updating", client_id)
            return

        client_old_tickers = client.tickers

        self._clients[client_id].tickers = tickers

        client_added_tickers = tickers - client_old_tickers
        client_removed_tickers = client_old_tickers - tickers

        old_tickers = set(self._tickers.keys())

        for ticker in client_added_tickers:
            self._tickers.setdefault(ticker.upper(), []).append(client_id)

        for ticker in client_removed_tickers:
            if ticker in self._tickers:
                self._tickers[ticker].remove(client_id)
                if not self._tickers[ticker]:
                    del self._tickers[ticker]

        new_tickers = set(self._tickers.keys())

        logger.debug(
            "Old tickers: %s, New tickers: %s",
            old_tickers,
            new_tickers,
        )

        if old_tickers != new_tickers:
            logger.debug(
                "Tickers changed, restarting task: old=%s, new=%s",
                old_tickers,
                new_tickers,
            )
            self._restart_task()

    def add_client(
        self,
        client_id: ClientId,
        tickers: set[TickerId],
        handler: HandlerFn | None = None,
    ):
        logger.debug("Adding client %s", client_id)
        if client_id not in self._clients:
            self._clients[client_id] = Client(
                tickers=tickers,
                handler=handler,
            )
            logger.info("Added new client %s", client_id)
        else:
            logger.warning("Client %s already exists", client_id)

        logger.info("CLIENTS: %s", self._clients)

    def drop_client(self, client_id: uuid.UUID) -> None:
        logger.debug("Dropping client %s", client_id)
        old_tickers = set(self._tickers.keys())
        if client_id in self._clients:
            for ticker in self._clients[client_id].tickers:
                self._tickers[ticker].remove(client_id)
                if not self._tickers[ticker]:
                    del self._tickers[ticker]
            del self._clients[client_id]
        else:
            logger.warning("Client %s not found", client_id)

        if old_tickers != set(self._tickers.keys()):
            logger.debug(
                "Tickers changed, restarting task: old=%s, new=%s",
                old_tickers,
                set(self._tickers.keys()),
            )
            self._restart_task()

        logger.info("CLIENTS: %s", self._clients)
