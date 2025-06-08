import asyncio
import logging
import uuid

from typing_extensions import override

from modules.authentication import clerk_auth
from modules.sse import clients, live_prices, parse_sse_request, subscribe, unsubscribe
from modules.sse.sse_consumer import SSEConsumer


class SSEConsumerImpl(SSEConsumer):

    def __init__(self, *args, **kwargs):
        """
        Initializes the SSEConsumerImpl instance and sets up the shutdown event used to control stream termination.
        """
        super().__init__(*args, **kwargs)
        self.shutdown_event = asyncio.Event()

    def log(self, level, msg):
        """
        Logs a message with the specified logging level, prefixed by the current connection ID.
        
        Args:
            level: The logging level (e.g., logging.INFO, logging.ERROR).
            msg: The message to log.
        """
        logging.log(level, f"{self.connection_id}: {msg}")

    async def live_prices_handler(self, prices: dict[str, float]) -> None:
        """
        Handles incoming live price updates for the current connection.
        
        Filters the provided prices to include only those relevant to the subscribed symbols for this connection, logs the filtered prices, and sends them as a "price_update" SSE event. If the connection ID is not set, the handler logs an error and exits without sending updates.
        """
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
        """
        Asynchronously validates a bearer token for authentication.
        
        Returns:
            True if the token is valid; False if authentication fails.
        """
        try:
            clerk_auth.validate_token(bearer_token)
            return True
        except clerk_auth.AuthenticationFailed as e:
            logging.error(f"Authentication failed: {e}")
            return False

    @override
    async def handle(self, params):
        """
        Handles the lifecycle of an SSE connection for live price updates.
        
        Parses and validates request parameters, subscribes the connection to requested symbols, registers a live price update handler, and waits for a shutdown event or cancellation. Cleans up subscriptions and handlers upon disconnection or error.
        """
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
        """
        Disconnects the SSE stream and performs cleanup.
        
        Signals the shutdown event to terminate the stream, unsubscribes the connection from all subscribed symbols, and invokes the superclass disconnect logic.
        """
        logging.debug(f"{self.connection_id}: Disconnecting SSE stream.")
        self.shutdown_event.set()
        unsubscribe(self.connection_id, clients.get(self.connection_id, set()))
        await super().disconnect()
