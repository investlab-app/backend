import asyncio
from abc import ABC, abstractmethod
from typing import Any, override
from urllib.parse import parse_qs

from channels.generic.http import AsyncHttpConsumer

from config.logging import get_logger
from config.settings import CORS_ALLOWED_ORIGINS

logger = get_logger(__name__)


class SSEConsumer(AsyncHttpConsumer, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sse_task = None
        self.shutdown_event = asyncio.Event()

    @staticmethod
    def _headers(response_origin: bytes | None):
        return [
            (b"Content-Type", b"text/event-stream"),
            (b"Cache-Control", b"no-cache"),
            (b"Connection", b"keep-alive"),
            (b"Access-Control-Allow-Origin", response_origin or b"*"),
            (b"Access-Control-Allow-Methods", b"GET, OPTIONS"),
            (b"Access-Control-Allow-Headers", b"Content-Type, Authorization"),
        ]

    async def handle_preflight(self, origin):
        origin_str = origin.decode("utf-8") if origin else ""
        response_origin = origin if origin_str in CORS_ALLOWED_ORIGINS else b""
        await self.send_response(
            status=204,
            headers=self._headers(response_origin),
            body=b"",
        )
        return None

    @staticmethod
    @abstractmethod
    async def _validate_auth(bearer_token: str) -> bool:
        """
        Validates the provided bearer token using Clerk authentication.
        :param bearer_token: The token to validate.
        :return: bool: True if the token is valid, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement _validate_auth method.")

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
            bearer_token = auth_header.split()[1]
        else:
            return await self.send_response(
                status=401,
                body=b"Unauthorized",
                headers=[(b"WWW-Authenticate", b"Bearer")],
            )

        if not await self._validate_auth(bearer_token.decode("utf-8")):
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

            if request_origin.decode("utf-8") in CORS_ALLOWED_ORIGINS:
                await self.send_headers(
                    headers=self._headers(request_origin), status=200
                )
                self.sse_task = await self.handle(params_decoded)
            else:
                await self.send_response(
                    status=403,
                    body=b"Access-Control-Allow-Origin not allowed",
                    headers=self._headers(None),
                )

        return None

    @abstractmethod
    @override
    async def handle(self, params):  # pylint: disable=arguments-renamed
        """
        This method should be implemented by subclasses to handle the SSE
        event stream. It will run as a background task.
        """
        raise NotImplementedError("Subclasses must implement the handle method.")

    async def send_event(self, event: str, data: Any) -> None:
        """Send an event to the client.

        Args:
            event: The event name.
            data: The event data.
        """
        tasks = asyncio.all_tasks()
        logger.info("Current tasks in event loop: %s", len(tasks))
        for task in tasks:
            logger.info(
                "Task: %s, Done: %s, Cancelled: %s",
                task.get_name(),
                task.done(),
                task.cancelled(),
            )

        event_data = f"event: {event}\ndata: {data}\n\n"
        await self.send(text_data=event_data)

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
                logger.info("SSE task was successfully cancelled.")
        await super().disconnect()
