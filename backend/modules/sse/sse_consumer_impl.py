import asyncio
import logging
import uuid

from typing_extensions import override

from modules.authentication import clerk_auth
from modules.sse import live_prices
from modules.sse.schemas import SSERequestParams
from modules.sse.sse_consumer import SSEConsumer


class SSEConsumerImpl(SSEConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutdown_event = asyncio.Event()
        self.connection_id: uuid.UUID | None = None
        self.log = logging.getLogger(__name__)

    async def live_prices_handler(self, prices: dict[str, any]) -> None:
        self.log.debug(f"Live prices handler called with prices: {prices}")

        if not self.connection_id:
            self.log.error("Connection ID is not set, cannot handle live prices.")
            return

        # Filter prices based on client subscriptions
        client_symbols = live_prices.clients.get(self.connection_id, set())
        filtered_prices = {
            symbol: price
            for symbol, price in prices.items()
            if symbol in client_symbols
        }

        if filtered_prices:
            await self.send_event("price_update", str(filtered_prices))

    @staticmethod
    @override
    async def _validate_auth(bearer_token: str) -> bool:
        try:
            clerk_auth.authenticate_and_get_user(bearer_token)
            return True
        except clerk_auth.AuthenticationFailed as e:
            logging.error(f"Authentication failed: {e}")
            return False

    @override
    async def handle(self, params):
        try:
            params = SSERequestParams.parse(params)
        except ValueError as e:
            self.log.error(f"Invalid SSE request parameters: {e}")
            raise

        self.connection_id = params.connection_id
        symbols = params.symbols

        self.log.debug(
            f"{self.connection_id}: Starting SSE stream with symbols: {symbols}"
        )

        try:
            live_prices.subscribe(self.connection_id, symbols, self.live_prices_handler)

            self.log.debug(f"{self.connection_id}: Waiting for SSE stream to finish")
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            self.log.debug(f"{self.connection_id}: Disconnected from SSE stream.")
            raise
        except Exception as e:
            self.log.error(
                f"{self.connection_id}: An error occurred in the stream: {e}"
            )
            raise
        finally:
            live_prices.unsubscribe(self.connection_id)
            self.log.debug("SSE stream generation finished.")

    async def disconnect(self):
        self.log.debug(f"{self.connection_id}: Disconnecting SSE stream.")
        self.shutdown_event.set()
        await super().disconnect()
