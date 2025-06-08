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
