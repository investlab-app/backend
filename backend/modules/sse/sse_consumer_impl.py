import asyncio
from typing import TYPE_CHECKING, Any, override

from asgiref.sync import sync_to_async
from dependency_injector.wiring import Provide, inject

from config.containers import AppContainer
from config.logging import get_logger
from modules.authentication import clerk_auth
from modules.sse.schemas import SSERequestParams
from modules.sse.services import SSEService
from modules.sse.sse_consumer import SSEConsumer

if TYPE_CHECKING:
    import uuid

logger = get_logger(__name__)


class SSEConsumerImpl(SSEConsumer):
    @inject
    def __init__(
        self,
        sse_service: SSEService = Provide[AppContainer.prices_container.sse_service],
    ):
        super().__init__()
        self.shutdown_event = asyncio.Event()
        self.connection_id: uuid.UUID | None = None
        self._sse_service: SSEService = sse_service

    def sse_handler(self, prices: dict[str, Any]) -> None:
        if not self.connection_id:
            logger.error("Connection ID is not set, cannot handle live prices.")
            return

        instrument_id = prices.get("id")
        if instrument_id is None:
            logger.warning("Received price update without 'id': %s", prices)
            return

        self.send_event(f"PRICE_UPDATE_{instrument_id}", str(prices))

    @staticmethod
    @override
    async def _validate_auth(token: str) -> bool:
        try:
            await sync_to_async(clerk_auth.verify_token)(token)
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
        events = params.events

        logger.debug(
            "%s: Starting SSE stream with events: %s", self.connection_id, events
        )

        self.send_event("connection_established", str(self.connection_id))

        try:
            self._sse_service.add_client(self.connection_id, self.sse_handler)
            self._sse_service.update(self.connection_id, events)

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
            self._sse_service.drop_client(self.connection_id)
            logger.debug("SSE stream generation finished.")

    async def disconnect(self):
        logger.debug("%s: Disconnecting SSE stream.", self.connection_id)
        self.shutdown_event.set()
        await super().disconnect()
