import asyncio
import logging
from abc import ABC, abstractmethod
from urllib.parse import parse_qs

from channels.generic.http import AsyncHttpConsumer
from typing_extensions import override

from config.settings import CORS_ALLOWED_ORIGINS


class SSEConsumer(AsyncHttpConsumer, ABC):

    def __init__(self, *args, **kwargs):
        """
        Initializes the SSEConsumer with attributes for managing SSE tasks and shutdown signaling.
        """
        super().__init__(*args, **kwargs)
        self.sse_task = None
        self.shutdown_event = asyncio.Event()

    @staticmethod
    def _headers(response_origin: bytes | None):
        """
        Generates HTTP headers required for Server-Sent Events (SSE) responses with CORS support.
        
        Args:
            response_origin: The origin to set for the Access-Control-Allow-Origin header, or None to allow all origins.
        
        Returns:
            A list of HTTP header tuples for SSE responses, including CORS and connection headers.
        """
        return [
            (b"Content-Type", b"text/event-stream"),
            (b"Cache-Control", b"no-cache"),
            (b"Connection", b"keep-alive"),
            (b"Access-Control-Allow-Origin", response_origin or b"*"),
            (b"Access-Control-Allow-Methods", b"GET, OPTIONS"),
            (b"Access-Control-Allow-Headers", b"Content-Type, Authorization"),
        ]

    async def handle_preflight(self, origin):
        """
        Handles CORS preflight (OPTIONS) requests by responding with appropriate headers.
        
        If the provided origin is allowed, includes it in the CORS response headers; otherwise, responds with a wildcard origin.
        """
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
        Validates the provided bearer token for authentication.
        
        This method must be implemented by subclasses to define custom authentication logic.
        
        Args:
            bearer_token: The bearer token extracted from the Authorization header.
        
        Returns:
            True if the token is valid; False otherwise.
        """
        raise NotImplementedError("Subclasses must implement validate_auth method.")

    async def http_request(self, message) -> None:
        """
        Handles incoming HTTP requests for establishing an SSE connection.
        
        Validates CORS origin and bearer token authentication, responds to preflight OPTIONS requests, and initiates the SSE event stream as a background task if authentication and CORS checks pass. Responds with appropriate HTTP status codes for unauthorized or disallowed origins.
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
                self.sse_task = asyncio.create_task(self.handle(params_decoded))
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
        Handles the SSE event stream as a background task.
        
        Subclasses must implement this method to define how events are generated and sent to the client using the provided query parameters.
        
        Args:
            params: Decoded query parameters from the HTTP request.
        """
        raise NotImplementedError("Subclasses must implement the handle method.")

    async def _send_event(self, event: str, data: str):
        """
        Sends a Server-Sent Event (SSE) with the specified event name and data to the client.
        
        Args:
            event: The SSE event type.
            data: The event payload as a string.
        """
        event_data = f"event: {event}\ndata: {data}\n\n"
        await self.send_body(event_data.encode("utf-8"), more_body=True)

    @override
    async def disconnect(self):
        """
        Cleans up resources and cancels the SSE background task when the client disconnects.
        """
        if self.sse_task and not self.sse_task.done():
            self.sse_task.cancel()
            self.shutdown_event.set()
            try:
                await self.sse_task
            except asyncio.CancelledError:
                logging.info("SSE task was successfully cancelled.")
        await super().disconnect()
