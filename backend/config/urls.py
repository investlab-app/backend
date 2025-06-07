import logging
import uuid

import asyncio
from django.contrib import admin
from django.urls import include, path
from django.utils.decorators import classonlymethod
from django.views.generic.base import View
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from typing_extensions import AsyncGenerator

from modules.core.views import StatusView

API_PREFIX = "api"

from django.http import StreamingHttpResponse, HttpRequest


import asyncio
import logging
import uuid
from typing import AsyncGenerator

# Assuming HttpRequest and StreamingHttpResponse are imported from django.http
# and django.views.decorators.http for async (if using @require_http_methods or similar)
from django.http import HttpRequest, StreamingHttpResponse

# Configure basic logging for visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class StreamTimerView(View):
    # @classonlymethod
    # def as_view(cls, **initkwargs):
    #     view = super().as_view(**initkwargs)
    #     view._is_coroutine = asyncio.iscoroutine
    #     return view

    async def get(self, request: HttpRequest, *args, **kwargs) -> StreamingHttpResponse:
# async def stream_timer(
#         request: HttpRequest, *args, **kwargs
# ) -> StreamingHttpResponse:
        print("StreamTimerView.get called")
        async def streamed_events() -> AsyncGenerator[str, None]:
            """
            "Listen for events and generate an SSE message for each event"
            """
            connection_id = uuid.uuid4()
            events_count = 0

            try:
                logging.info(
                    f"{connection_id}: Connecting to stream."
                )
                while True:
                    events_count += 1

                    # Correct way to format the data line using an f-string
                    # No need for .format() after this
                    event_data = f"event: new\n" \
                                 f"data: {events_count}\n\n"

                    logging.info(
                        f"{connection_id}: Sent event {events_count}."
                    )

                    # Yield the correctly formatted event string
                    yield event_data

                    await asyncio.sleep(1) # Send an event every second

            except asyncio.CancelledError:
                # This happens when the client disconnects or the server is shut down
                logging.info(
                    f"{connection_id}: Disconnected after {events_count} events."
                )
            except Exception as e:
                # Catch other potential errors
                logging.error(f"{connection_id}: An error occurred: {e}")
            finally:
                logging.info(f"{connection_id}: Stream generation finished.")


        # Ensure these headers are set correctly
        response = StreamingHttpResponse(
            streamed_events(),
            headers={
                "Cache-Control": "no-cache",  # Prevent caching of the stream
                "Connection": "keep-alive",   # Keep the connection open
                "Content-Type": "text/event-stream", # Crucial for SSE parsing
                # Add CORS header if your frontend is on a different origin
                "Access-Control-Allow-Origin": "*",
            }
        )
        # This might be needed for some WSGI servers, but usually not with ASGI.
        # response['X-Accel-Buffering'] = 'no' # For Nginx to prevent buffering

        return response

urlpatterns = [
    # path("events/", include(django_eventstream.urls), {"channels": ["test"]}),
    path(f"{API_PREFIX}/sse/", StreamTimerView.as_view(), name="stream_time"),
    path(f"{API_PREFIX}/admin/", admin.site.urls),
    path(f"{API_PREFIX}/status/", StatusView.as_view(), name="status"),
    # Docs
    path(
        f"{API_PREFIX}/schema/",
        SpectacularAPIView.as_view(authentication_classes=[]),
        name="schema",
    ),
    path(
        f"{API_PREFIX}/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=[],
        ),
        name="swagger",
    ),
    path(
        f"{API_PREFIX}/redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
            authentication_classes=[],
        ),
        name="redoc",
    ),
    # Modules
    path(f"{API_PREFIX}/prices/", include("modules.prices.urls")),
    path(f"{API_PREFIX}/instruments/", include("modules.instruments.urls")),
    path(f"{API_PREFIX}/auth/", include("modules.authentication.urls")),
    path(f"{API_PREFIX}/test/", include("modules.core.urls")),
]
