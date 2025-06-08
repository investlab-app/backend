import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from urllib.parse import parse_qs

from channels.generic.http import AsyncHttpConsumer
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from pydantic import BaseModel, Field
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from typing_extensions import override

from config.settings import CORS_ALLOWED_ORIGINS
from modules.authentication import clerk_auth
from modules.prices.services import LivePrices


class SSEConsumer(AsyncHttpConsumer, ABC):
    sse_headers = [
        (b"Content-Type", b"text/event-stream"),
        (b"Cache-Control", b"no-cache"),
        (b"Connection", b"keep-alive"),
        (b"Access-Control-Allow-Credentials", b"true"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sse_task = None
        self.shutdown_event = asyncio.Event()

    async def handle_preflight(self, origin):
        response_origin = (
            origin if origin.decode("utf-8") in CORS_ALLOWED_ORIGINS else b""
        )
        headers = [
            (b"Access-Control-Allow-Origin", response_origin),
            (b"Access-Control-Allow-Methods", b"GET, OPTIONS"),
            (b"Access-Control-Allow-Headers", b"Content-Type, Authorization"),
            (b"Access-Control-Allow-Credentials", b"true"),
        ]
        await self.send_response(
            status=204,
            headers=headers,
            body=b"",
        )
        print(headers)
        return None

    @staticmethod
    @abstractmethod
    async def validate_auth(bearer_token: str) -> bool:
        """
        Validates the provided bearer token using Clerk authentication.
        :param bearer_token: The token to validate.
        :return: bool: True if the token is valid, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement validate_auth method.")

    async def http_request(self, message) -> None:
        """
        Async entrypoint for the HTTP request.
        This method now sets up the SSE connection and starts a background
        task to send events, rather than blocking.
        """
        headers: dict[bytes, bytes] = dict(self.scope["headers"])
        request_origin = headers.get(b"origin", b"")

        if self.scope["method"] == "OPTIONS":
            return await self.handle_preflight(request_origin)

        auth_header = headers.get(b"authorization", b"")
        if auth_header.startswith(b"Bearer "):
            bearer_token = auth_header[7:]
        else:
            return await self.send_response(
                status=401,
                body=b"Unauthorized",
                headers=[(b"WWW-Authenticate", b"Bearer")],
            )

        if not await self.validate_auth(bearer_token.decode("utf-8")):
            return await self.send_response(
                status=401,
                body=b"Unauthorized",
                headers=[(b"WWW-Authenticate", b"Bearer")],
            )

        if "body" in message:
            self.body.append(message["body"])

        if not message.get("more_body"):
            query_string = self.scope["query_string"]
            params: dict[bytes, list[bytes]] = parse_qs(query_string)
            params_decoded = {
                k.decode("utf-8"): v[0].decode("utf-8") for k, v in params.items()
            }

            response_headers = self.sse_headers.copy()

            allowed = request_origin.decode("utf-8") in CORS_ALLOWED_ORIGINS

            if allowed:
                response_headers.append(
                    (b"Access-Control-Allow-Origin", request_origin)
                )

            print(f"Response headers: {response_headers}")

            await self.send_headers(
                status=200,
                headers=response_headers,
            )

            if allowed:
                self.sse_task = asyncio.create_task(self.handle(params_decoded))

        return None

    @abstractmethod
    @override
    async def handle(self, params):  # pylint: disable=arguments-renamed
        """
        This method should be implemented by subclasses to handle the SSE
        event stream. It will run as a background task.
        """
        raise NotImplementedError("Subclasses must implement the handle method.")

    async def _send_event(self, event: str, data: str):
        """
        Sends an event to the client.
        :param event: The channel name for the event.
        :param data: The data to send in the event.
        """
        event_data = f"event: {event}\ndata: {data}\n\n"
        await self.send_body(event_data.encode("utf-8"), more_body=True)

    @override
    async def disconnect(self):
        """
        Called when the client disconnects.
        This is responsible for cleaning up the background task.
        """
        if self.sse_task and not self.sse_task.done():
            self.sse_task.cancel()
            self.shutdown_event.set()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                logging.info("SSE task was successfully cancelled.")
        await super().disconnect()


subscriptions: dict[str, int] = {}
clients = dict[uuid.UUID, set[str]]()
live_prices = LivePrices()


def subscribe(client_id: uuid.UUID, symbols: set[str]) -> None:
    for symbol in iter(symbols):
        subscriptions.setdefault(symbol, 0)
        subscriptions[symbol] += 1

    client_symbols = clients.get(client_id, set())
    clients.update({client_id: symbols | client_symbols})

    live_prices.add_instruments(symbols)


def unsubscribe(client_id: uuid.UUID, symbols: set[str]) -> None:
    for symbol in iter(symbols):
        if subscriptions[symbol] > 1:
            subscriptions[symbol] -= 1
        elif subscriptions[symbol] == 1:
            del subscriptions[symbol]
            live_prices.remove_instruments({symbol})

    client_symbols = clients.get(client_id, set())
    clients.update({client_id: symbols - client_symbols})

    live_prices.remove_instruments(symbols)


class SSERequestSerializer(serializers.Serializer):
    @override
    def to_internal_value(self, data):
        symbols = data.get("symbols")
        if isinstance(symbols, str):
            symbols = [s.strip() for s in symbols.split(",") if s.strip()]
        data["symbols"] = symbols
        return super().to_internal_value(data)

    symbols = serializers.ListField(
        child=serializers.CharField(
            help_text="List of stock symbols to subscribe to, e.g. ['AAPL', 'GOOGL']."
        ),
        required=True,
        help_text="Comma-separated list of ticker symbols (e.g., 'AAPL,MSFT,GOOG').",
    )
    connectionId = serializers.UUIDField(
        required=True, help_text="Unique identifier for the SSE connection."
    )


class SSERequestParams(BaseModel):
    symbols: set[str]
    connection_id: uuid.UUID = Field(..., alias="connectionId")

    class Config:
        populate_by_name = True


def parse_sse_request(data: dict) -> SSERequestParams:
    serializer = SSERequestSerializer(data=data)

    if not serializer.is_valid():
        raise ValueError(f"Invalid SSE request data: {serializer.errors}")

    return SSERequestParams.model_validate(serializer.validated_data)


class SSESubscribeView(APIView):
    @extend_schema(request=SSERequestSerializer)
    def put(self, request):
        try:
            params = parse_sse_request(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        connection_id = params.connection_id
        symbols = params.symbols

        subscribe(connection_id, symbols)

        logging.debug(f"{connection_id}: Subscribed to symbols: {symbols}")

        return HttpResponse(
            f"Subscribed to new events: {symbols}",
            content_type="text/plain",
            status=200,
        )


class SSEUnsubscribeView(APIView):
    @extend_schema(request=SSERequestSerializer)
    def put(self, request):
        try:
            params = parse_sse_request(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        connection_id = params.connection_id
        symbols = params.symbols

        unsubscribe(connection_id, symbols)

        logging.debug(f"{connection_id}: Unsubscribed from symbols: {symbols}")

        return HttpResponse(
            f"Unsubscribed from events: {symbols}",
            content_type="text/plain",
            status=200,
        )


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

        await self._send_event("price_update", str(prices))

    connection_id: uuid.UUID | None = None

    @staticmethod
    @override
    async def validate_auth(bearer_token: str) -> bool:
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

        try:
            subscribe(self.connection_id, symbols)
            if clients[self.connection_id]:
                live_prices.add_handler(self.live_prices_handler)

            await self.shutdown_event.wait()
        except asyncio.CancelledError:
            logging.debug(f"{self.connection_id}: Disconnected from SSE stream.")
            raise
        except Exception as e:
            logging.error(f"{self.connection_id}: An error occurred in the stream: {e}")
            raise
        finally:
            self.log(logging.DEBUG, "SSE stream generation finished.")

    async def disconnect(self):
        logging.debug(f"{self.connection_id}: Disconnecting SSE stream.")
        self.shutdown_event.set()
        unsubscribe(self.connection_id, clients.get(self.connection_id, set()))
        await super().disconnect()
