import logging

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.sse import live_prices
from modules.sse.schemas import SSERequestParams
from modules.sse.serializers import (
    SSERequestSerializer,
    SSEResponseSerializer,
    SSEErrorResponseSerializer,
)


class SSESubscribeView(APIView):
    serializer_class = SSERequestSerializer
    
    @extend_schema(
        request=SSERequestSerializer,
        responses={
            200: OpenApiResponse(
                response=SSEResponseSerializer,
                description="Successfully subscribed to symbols"
            ),
            400: OpenApiResponse(
                response=SSEErrorResponseSerializer,
                description="Invalid request data"
            ),
            500: OpenApiResponse(
                response=SSEErrorResponseSerializer,
                description="Internal server error"
            ),
        },
        summary="Subscribe to SSE events for stock symbols",
        description="Subscribe to Server-Sent Events for real-time stock price updates for specified symbols.",
    )
    def put(self, request):
        try:
            params = SSERequestParams.parse(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        connection_id = params.connection_id
        symbols = params.symbols

        try:
            live_prices.subscribe(connection_id, symbols)
            logging.debug(f"{connection_id}: Subscribed to symbols: {symbols}")
            return Response(
                {"message": f"Subscribed to new events: {symbols}"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logging.error(
                f"{connection_id}: Failed to subscribe to symbols {symbols}: {str(e)}"
            )
            return Response(
                {"error": f"Failed to subscribe to symbols: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SSEUnsubscribeView(APIView):
    serializer_class = SSERequestSerializer
    
    @extend_schema(
        request=SSERequestSerializer,
        responses={
            200: OpenApiResponse(
                response=SSEResponseSerializer,
                description="Successfully unsubscribed from symbols"
            ),
            400: OpenApiResponse(
                response=SSEErrorResponseSerializer,
                description="Invalid request data"
            ),
            500: OpenApiResponse(
                response=SSEErrorResponseSerializer,
                description="Internal server error"
            ),
        },
        summary="Unsubscribe from SSE events for stock symbols",
        description="Unsubscribe from Server-Sent Events for specified stock symbols.",
    )
    def put(self, request):
        try:
            params = SSERequestParams.parse(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        connection_id = params.connection_id
        symbols = params.symbols

        try:
            live_prices.unsubscribe(connection_id, symbols)
            logging.debug(f"{connection_id}: Unsubscribed from symbols: {symbols}")
            return Response(
                {"message": f"Unsubscribed from events: {symbols}"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logging.error(
                f"{connection_id}: Failed to unsubscribe from symbols {symbols}: {str(e)}"
            )
            return Response(
                {"error": f"Failed to unsubscribe from symbols: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
