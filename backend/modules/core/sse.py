import asyncio
import json
import time
from datetime import datetime
from urllib.parse import parse_qs
from abc import ABC, abstractmethod

from django.http import StreamingHttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class BaseSSEView(View):
    """
    Base class for Server-Sent Events (SSE) views using Django's StreamingHttpResponse.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Cache-Control, Authorization",
        }
        
        self.default_headers = {
            "Cache-Control": "no-cache",
            "Content-Type": "text/event-stream",
            **self.cors_headers,
        }

        self.queue = asyncio.Queue()
    
    async def ticker(delay, to):
        """Yield numbers from 0 to `to` every `delay` seconds."""
        for i in range(to):
            yield i
            await asyncio.sleep(delay)

    async def event_stream(self, params):
        async for _ in self.ticker(10):
            try:
                message = {
                    "type": "sse",
                    "data": {
                        "timestamp": datetime.now().isoformat(),
                        "params": params,
                    },
                }
                
                custom_data = self.get_sse_data()
                if custom_data:
                    message["data"].update(custom_data)
                
                event = f"data: {json.dumps(message)}\n\n"
                print(f"Sending SSE message")
                yield event
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in SSE stream: {e}")
                break

    def get(self, request, *args, **kwargs):
        params = self._parse_query_params(request)

        self.queue.put_nowait(params)

        response = StreamingHttpResponse(self.event_stream(params))
        for key, value in self.default_headers.items():
            response[key] = value
            
        return response

    def get_sse_data(self):
        return {
            "message": "This is a base SSE view. Override get_sse_data method."
        }

    def _parse_query_params(self, request) -> dict[str, list]:
        query_string = request.META.get('QUERY_STRING', '')
        return parse_qs(query_string)
