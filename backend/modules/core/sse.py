import logging
import uuid
from abc import ABC, abstractmethod
from urllib.parse import parse_qs

import asyncio
import yfinance
from channels.generic.http import AsyncHttpConsumer
from django.http import HttpResponseBadRequest, HttpResponse
from django.views.generic.base import View
from typing_extensions import override

from config.settings import CORS_ALLOWED_ORIGINS


class ServerSentEventsConsumer(AsyncHttpConsumer, ABC):
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
            headers = dict(self.scope["headers"])
            request_origin = headers.get(b'origin')

            params = parse_qs(self.scope["query_string"])
            params = {k.decode("utf-8"): v[0].decode("utf-8") for k, v in params.items()}

            response_headers = [
                (b"Content-Type", b"text/event-stream"),
                (b"Cache-Control", b"no-cache"),
                (b"Connection", b"keep-alive"),
            ]

            allowed = request_origin and request_origin.decode("utf-8") in CORS_ALLOWED_ORIGINS

            if allowed:
                response_headers.append((b"Access-Control-Allow-Origin", request_origin))

            await self.send_headers(
                status=200,
                headers=response_headers,
            )

            if allowed:
                self.sse_task = asyncio.create_task(self.handle(params))

            self.shutdown_event.wait()

    @abstractmethod
    async def handle(self, params):
        """
        This method should be implemented by subclasses to handle the SSE
        event stream. It will run as a background task.
        """
        raise NotImplementedError("Subclasses must implement the handle method.")


    @override
    async def disconnect(self):
        """
        Called when the client disconnects.
        This is responsible for cleaning up the background task.
        """
        logging.info("Client disconnected. Cleaning up SSE task.")
        if self.sse_task and not self.sse_task.done():
            self.sse_task.cancel()
            self.shutdown_event.set()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                logging.info("SSE task was successfully cancelled.")
        await super().disconnect()


subscriptions: dict[uuid.UUID, list[str]] = {}

clients = dict[uuid.UUID, ServerSentEventsConsumer]()

class SSESubscribeView(View):
    """
    A view that handles subscriptions to Server-Sent Events (SSE).
    This view is responsible for setting up the SSE connection and starting
    the event stream.
    """

    def get(self, request):
        """
        Handles GET requests to initiate an SSE connection.
        """
        body = request.GET.dict()
        if not body:
            return HttpResponseBadRequest("No subscription parameters provided.")

        subscriptions = body.get("subscriptions", None)
        if not subscriptions:
            return HttpResponseBadRequest("No subscriptions provided.")

        connection_id = uuid.uuid4()
        subscriptions[connection_id] = subscriptions

        return HttpResponse(
            f"Subscribed to SSE with connection ID: {connection_id}",
            content_type="text/plain",
            status=200
        )

class SSEUnsubscribeView(View):
    """
    A view that handles unsubscriptions from Server-Sent Events (SSE).
    This view is responsible for cleaning up the subscription.
    """

    def get(self, request, connection_id):
        """
        Handles GET requests to unsubscribe from SSE.
        """
        try:
            connection_id = uuid.UUID(connection_id)
            if connection_id in subscriptions:
                del subscriptions[connection_id]
                return HttpResponse(
                    f"Unsubscribed from SSE with connection ID: {connection_id}",
                    content_type="text/plain",
                    status=200
                )
            else:
                return HttpResponseBadRequest("Invalid connection ID.")
        except ValueError:
            return HttpResponseBadRequest("Invalid connection ID format.")


class SSEConsumerImpl(ServerSentEventsConsumer):

    symbols = []

    def live_handler(self, event):
        print(event)


    @override
    async def handle(self, params):
        """
        This method runs as a background task, sending events to the client
        in a loop until it's cancelled.
        """
        connection_id = uuid.uuid4() # todo add auth

        print(params)

        subscriptions[connection_id] = params.get("symbols", [])

        print(subscriptions[connection_id])

        if subscriptions[connection_id]:
            # create new background tasks to send events for each subscription
            # yfinance.Tickers(subscriptions[connection_id]).live(self.live_handler)
            fake_handler()







         #
        #
        #
        #
        #
        #
        #
        #
        #
        # events_count = 0
        #
        # try:
        #     logging.info(f"{connection_id}: Starting SSE event stream.")
        #     while True:
        #         # Simulate sending an event every second
        #         events_count += 1
        #         event_data = f"event: new\ndata: {events_count}\n\n"
        #         logging.info(f"{connection_id}: Sent event {events_count}.")
        #         await self.send_body(event_data.encode("utf-8"), more_body=True)
        #         await asyncio.sleep(1)
        #
        # except asyncio.CancelledError:
        #     logging.info(
        #         f"{connection_id}: Disconnected after sending {events_count} events."
        #     )
        #     raise
        #
        # except Exception as e:
        #     logging.error(f"{connection_id}: An error occurred in the stream: {e}")
        # finally:
        #     logging.info(f"{connection_id}: SSE stream generation finished.")
