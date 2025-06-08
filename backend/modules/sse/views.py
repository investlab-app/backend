import logging

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.sse import SSERequestSerializer, parse_sse_request, subscribe, unsubscribe


class SSESubscribeView(APIView):
    @extend_schema(request=SSERequestSerializer)
    def put(self, request):
        """
        Handles a PUT request to subscribe a client to Server-Sent Events (SSE) for specified symbols.
        
        Parses and validates the request data, registers the connection for the requested symbols, and returns a confirmation message. Returns a 400 Bad Request response if the request data is invalid.
        """
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
        """
        Handles HTTP PUT requests to unsubscribe a client from specified SSE event symbols.
        
        Parses the request data to extract the connection ID and symbols, removes the subscription for those symbols, and returns a plain text confirmation response. Returns a 400 Bad Request if the request data is invalid.
        """
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
