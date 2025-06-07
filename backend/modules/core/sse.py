import uuid
import logging
from abc import ABC, abstractmethod
from urllib.parse import parse_qs

import asyncio
from channels.generic.http import AsyncHttpConsumer
from django.http import HttpResponse
from django.views.generic.base import View
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from typing_extensions import override

from config.settings import CORS_ALLOWED_ORIGINS
from modules.prices.services import LivePrices


class ServerSentEventsConsumer(AsyncHttpConsumer, ABC):

    sse_headers = [
        (b"Content-Type", b"text/event-stream"),
        (b"Cache-Control", b"no-cache"),
        (b"Connection", b"keep-alive"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sse_task = None
        self.shutdown_event = asyncio.Event()

    @override
    async def http_request(self, message):
        """
        Async entrypoint for the HTTP request.
        This method now sets up the SSE connection and starts a background
        task to send events, rather than blocking.
        """
        if "body" in message:
            self.body.append(message["body"])

        if not message.get("more_body"):
            headers: dict[bytes, bytes] = dict(self.scope["headers"])
            request_origin = headers.get(b'origin')

            query_string = self.scope["query_string"]
            params = parse_qs(query_string)
            params_decoded = {k.decode("utf-8"): v[0].decode("utf-8") for k, v in params.items()}

            allowed = request_origin and request_origin.decode("utf-8") in CORS_ALLOWED_ORIGINS

            response_headers = self.sse_headers.copy()

            if allowed:
                response_headers.append((b"Access-Control-Allow-Origin", request_origin))

            await self.send_headers(
                status=200,
                headers=response_headers,
            )

            if allowed:
                self.sse_task = asyncio.create_task(self.handle(params_decoded))

    @abstractmethod
    async def handle(self, params):
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

def subscribe(client_id: uuid, symbols: set[str]) -> None:
    for symbol in symbols:
        subscriptions.setdefault(symbol, 0)
        subscriptions[symbol] += 1

    client_symbols = clients.get(client_id, set())
    clients.update({client_id: symbols | client_symbols})


def unsubscribe(client_id: uuid, symbols: set[str]) -> None:
    for symbol in symbols:
        if subscriptions[symbol] > 1:
            subscriptions[symbol] -= 1
        elif subscriptions[symbol] == 1:
            del subscriptions[symbol]

    client_symbols = clients.get(client_id, set())
    clients.update({client_id: symbols - client_symbols})


class SSESubscribeView(APIView):
    def put(self, request, symbols):
        symbols_set = set(symbols.split(","))

        client_id = uuid.uuid4()  # from clerk

        subscribe(client_id, symbols_set)

        logging.debug(f"{client_id}: Subscribed to symbols: {symbols_set}")

        return HttpResponse(
            f"Subscribed to new events: {symbols_set}",
            content_type="text/plain",
            status=200
        )


class SSEUnsubscribeView(View):
    def put(self, request, symbols):
        symbols_set = set(symbols.split(","))

        client_id = uuid.uuid4()  # from clerk

        unsubscribe(client_id, symbols_set)

        logging.debug(f"{client_id}: Unsubscribed from symbols: {symbols_set}")

        return HttpResponse(
            f"Unsubscribed from events: {symbols_set}",
            content_type="text/plain",
            status=200
        )


live_prices = LivePrices()

class SSEConsumerImpl(ServerSentEventsConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shutdown_event = asyncio.Event()

    def log(self, level, msg):
        logging.log(level, f"{self.connection_id}: {msg}")

    async def live_prices_handler(self, prices: dict[str, float]) -> None:
        prices = {label: price for (label, price) in prices.items() if label in clients[self.connection_id]}
        await self._send_event("price_update", prices.__str__())

    connection_id: uuid.UUID = None

    @override
    async def handle(self, params):
        self.connection_id = uuid.uuid4()  # todo add auth
        self.log(logging.DEBUG, f"{self.connection_id}: Starting SSE stream with params: {params}")
        try:
            symbols = params.get("symbols", "")
            if not symbols:
                self.log(logging.ERROR, "No symbols provided for SSE stream.")
            else:
                symbols_set = set(symbols.split(","))
                subscribe(self.connection_id, symbols_set)
                if clients[self.connection_id]:
                    live_prices.add_handler(self.live_prices_handler)
                    live_prices.add_instruments(set(clients[self.connection_id]))

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
        self._cleanup_symbols()
        await super().disconnect()

    def _cleanup_symbols(self):
        remove_symbols = []
        for symbol in clients.get(self.connection_id, []):
            subscriptions[symbol] -= 1
            if subscriptions[symbol] <= 0:
                remove_symbols += [symbol]
        logging.debug(f"{self.connection_id}: Cleaning up symbols: {remove_symbols}")
        live_prices.remove_instruments(set(remove_symbols))
