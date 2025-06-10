import asyncio
import logging
import uuid

from typing_extensions import override

from modules.sse.schemas import SSERequestParams
from modules.authentication import clerk_auth
from modules.sse import live_prices
from modules.sse.sse_consumer import SSEConsumer


class SSEConsumerImpl(SSEConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutdown_event = asyncio.Event()
        self.connection_id: uuid.UUID | None = None

    def live_prices_handler(self, prices: dict[str, any]) -> None:
        logging.debug(f"Live prices handler called with prices: {prices}")

        if not self.connection_id:
            logging.error("Connection ID is not set, cannot handle live prices.")
            return

        self.send_event("price_update", str(prices))

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
            logging.error(f"Invalid SSE request parameters: {e}")
            raise

        self.connection_id = params.connection_id
        symbols = params.symbols

        logging.debug(f"{self.connection_id}: Starting SSE stream with symbols: {symbols}")

        try:
            live_prices.subscribe(self.connection_id, symbols, self.live_prices_handler)

            logging.debug(f"{self.connection_id}: Waiting for SSE stream to finish")
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            logging.debug(f"{self.connection_id}: Disconnected from SSE stream.")
            raise
        except Exception as e:
            logging.error(f"{self.connection_id}: An error occurred in the stream: {e}")
            raise
        finally:
            live_prices.unsubscribe(self.connection_id)
            self.log(logging.DEBUG, "SSE stream generation finished.")

    async def disconnect(self):
        logging.debug(f"{self.connection_id}: Disconnecting SSE stream.")
        self.shutdown_event.set()
        await super().disconnect()
