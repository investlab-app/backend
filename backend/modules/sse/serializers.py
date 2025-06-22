from typing import override

from rest_framework import serializers


class SSERequestSerializer(serializers.Serializer):
    """Serializer for SSE request parameters."""

    @override
    def to_internal_value(self, data):
        data_copy = data.copy()

        symbols = data_copy.get("symbols")

        if isinstance(symbols, str):
            symbols = [s.strip() for s in symbols.split(",") if s.strip()]
        elif isinstance(symbols, list):
            symbols = [s.strip() for s in symbols if isinstance(s, str) and s.strip()]
        else:
            symbols = []

        data_copy["symbols"] = set(symbols)

        connection_id = data_copy.get("connectionId")
        if connection_id:
            data_copy["connection_id"] = connection_id

        return super().to_internal_value(data_copy)

    symbols = serializers.ListField(
        child=serializers.CharField(
            help_text="List of stock symbols to subscribe to, e.g. ['AAPL', 'GOOGL']."
        ),
        required=True,
        help_text="Comma-separated list of ticker symbols (e.g., 'AAPL,MSFT,GOOG').",
    )
    connection_id = serializers.UUIDField(
        required=True,
        help_text="Unique identifier for the SSE connection.",
    )


class SSEResponseSerializer(serializers.Serializer):
    """Serializer for SSE operation responses"""
    message = serializers.CharField(
        help_text="Response message indicating the result of the operation"
    )


class SSEErrorResponseSerializer(serializers.Serializer):
    """Serializer for SSE error responses"""
    error = serializers.CharField(
        help_text="Error message describing what went wrong"
    )


class StatusResponseSerializer(serializers.Serializer):
    """Serializer for status endpoint response"""
    message = serializers.CharField(
        help_text="Status message indicating the application is running"
    )
