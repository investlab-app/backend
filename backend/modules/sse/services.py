import asyncio
import re
import threading
import uuid

import yfinance

from config.logging import get_logger
from modules.prices.schemas import (
    Client,
    ClientId,
    HandlerFn,
    TickerId,
)

PRICE_UPDATE_PATTERN = re.compile(r"PRICE_UPDATE_(.+)")

logger = get_logger(__name__)


class SSEService:
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
        events: set[str],
    ) -> None:
        print(f"events: {events}")
        tickers = {
            symbol
            for event in events
            if (match := PRICE_UPDATE_PATTERN.match(event)) is not None
            and (symbol := match.group(1)) is not None
        }

        logger.debug("Updating client %s with events: %s", client_id, tickers)

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
        handler: HandlerFn | None = None,
    ):
        logger.debug("Adding client %s", client_id)
        if client_id not in self._clients:
            self._clients[client_id] = Client(
                tickers=set(),
                handler=handler,
            )
            logger.info("Added new client %s", client_id)
        else:
            logger.warning("Client %s already exists", client_id)

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
