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
        data_copy["symbols"] = symbols
        return super().to_internal_value(data_copy)

    symbols = serializers.ListField(
        child=serializers.CharField(
            help_text="List of stock symbols to subscribe to, e.g. ['AAPL', 'GOOGL']."
        ),
        required=True,
        help_text="Comma-separated list of ticker symbols (e.g., 'AAPL,MSFT,GOOG').",
    )
    connection_id = serializers.UUIDField(
        required=True, help_text="Unique identifier for the SSE connection."
    )
