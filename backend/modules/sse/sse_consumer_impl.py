import asyncio
from typing import TYPE_CHECKING, Any, override

from dependency_injector.wiring import Provide, inject

from config.containers import AppContainer
from config.logging import get_logger
from modules.authentication import clerk_auth
from modules.prices.services import LivePricesService
from modules.sse.schemas import SSERequestParams
from modules.sse.sse_consumer import SSEConsumer

if TYPE_CHECKING:
    import uuid

logger = get_logger(__name__)


class SSEConsumerImpl(SSEConsumer):
    @inject
    def __init__(
        self,
        live_prices: LivePricesService = Provide[
            AppContainer.prices_container.live_prices
        ],
    ):
        super().__init__()
        self.shutdown_event = asyncio.Event()
        self.connection_id: uuid.UUID | None = None
        self._live_prices: LivePricesService = live_prices

    def live_prices_handler(self, prices: dict[str, Any]) -> None:
        if not self.connection_id:
            logger.error("Connection ID is not set, cannot handle live prices.")
            return

        self.send_event("price_update", str(prices))

    @staticmethod
    @override
    async def _validate_auth(token: str) -> bool:
        try:
            clerk_auth.verify_token(token)
            return True
        except clerk_auth.AuthenticationFailed as e:
            logger.error("Authentication failed: %s", e)
            return False

    @override
    async def handle(self, params):
        try:
            params = SSERequestParams.parse(params)
        except ValueError as e:
            logger.error("Invalid SSE request parameters: %s", e)
            raise

        self.connection_id = params.connection_id
        symbols = params.symbols

        logger.debug(
            "%s: Starting SSE stream with symbols: %s", self.connection_id, symbols
        )

        self.send_event("connection_established", str(self.connection_id))

        try:
            self._live_prices.add_client(
                self.connection_id, symbols, self.live_prices_handler
            )

            logger.debug("%s: Waiting for SSE stream to finish", self.connection_id)
            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            logger.debug("%s: Disconnected from SSE stream.", self.connection_id)
            raise
        except Exception as e:
            logger.error(
                "%s: An error occurred in the stream: %s", self.connection_id, e
            )
            raise
        finally:
            # TODO(mikolajkapica): #26 Drop clients when disconnecting  # noqa: FIX002
            # This cannot be done right now since the connnection isnt dropped quickly
            # enough and this is showing by throwing this warning:
            # backend-1  | 2025-06-20 15:01:50,853 - daphne.server - WARNING -
            # Application instance <Task pending name='Task-10' coro=<ASGIStaticFilesHan
            # dler.__call__() running at /backend/.venv/lib/python3.13/site-packages/dja
            # ngo/contrib/staticfiles/handlers.py:101> wait_for=<Future pending cb=[Task
            # .task_wakeup()]>> for connection <WebRequest at 0x72e52a228a50 method=GET
            # uri=/api/sse?symbols=&connectionId=95d70fb1-728d-41b3-9750-cc6c8fe20113 cl
            # ientproto=HTTP/1.1> took too long to shut down and was killed.
            self._live_prices.drop_client(self.connection_id)
            logger.debug("SSE stream generation finished.")

    async def disconnect(self):
        logger.debug("%s: Disconnecting SSE stream.", self.connection_id)
        self.shutdown_event.set()
        await super().disconnect()
