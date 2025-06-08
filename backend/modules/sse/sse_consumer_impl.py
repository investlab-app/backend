import asyncio
import logging
import uuid

from typing_extensions import override

from modules.authentication import clerk_auth
from modules.sse import clients, live_prices, parse_sse_request, subscribe, unsubscribe
from modules.sse.sse_consumer import SSEConsumer


class SSEConsumerImpl(SSEConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutdown_event = asyncio.Event()

    def log(self, level, msg):
        logging.log(level, f"{self.connection_id}: {msg}")

    async def live_prices_handler(self, prices: dict[str, float]) -> None:
        if not self.connection_id:
            logging.error("Connection ID is not set, cannot handle live prices.")
            return

        prices = {
            label: price
            for (label, price) in prices.items()
            if label in clients[self.connection_id]
        }

        self.log(logging.DEBUG, "Received live prices: " + str(prices))

        await self._send_event("price_update", str(prices))

    connection_id: uuid.UUID | None = None

    @staticmethod
    @override
    async def _validate_auth(bearer_token: str) -> bool:
        try:
            clerk_auth.validate_token(bearer_token)
            return True
        except clerk_auth.AuthenticationFailed as e:
            logging.error(f"Authentication failed: {e}")
            return False

    @override
    async def handle(self, params):
        try:
            params = parse_sse_request(params)
        except ValueError as e:
            logging.error(f"Invalid SSE request parameters: {e}")
            raise

        self.connection_id = params.connection_id
        symbols = params.symbols
        self.log(
            logging.DEBUG,
            f"{self.connection_id}: Starting SSE stream with symbols: {symbols}",
        )

        handler_added = False
        try:
            subscribe(self.connection_id, symbols)
            if clients[self.connection_id]:
                live_prices.add_handler(self.live_prices_handler)
                handler_added = True

            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            logging.debug(f"{self.connection_id}: Disconnected from SSE stream.")
            raise
        except Exception as e:
            logging.error(f"{self.connection_id}: An error occurred in the stream: {e}")
            raise
        finally:
            if handler_added:
                live_prices.remove_handler(self.live_prices_handler)
            self.log(logging.DEBUG, "SSE stream generation finished.")

    async def disconnect(self):
        logging.debug(f"{self.connection_id}: Disconnecting SSE stream.")
        self.shutdown_event.set()
        unsubscribe(self.connection_id, clients.get(self.connection_id, set()))
        await super().disconnect()
