from rest_framework import serializers


class SSERequestSerializer(serializers.Serializer):
    """Serializer for SSE request parameters."""

    def to_internal_value(self, data: dict) -> dict:
        data_copy = data.copy()

        events = data_copy.get("events")

        if isinstance(events, str):
            events = [s.strip() for s in events.split(",") if s.strip()]
        elif isinstance(events, list):
            events = [s.strip() for s in events if isinstance(s, str) and s.strip()]
        else:
            events = []

        data_copy["events"] = set(events)

        connection_id = data_copy.get("connectionId")
        if connection_id:
            data_copy["connection_id"] = connection_id

        return super().to_internal_value(data_copy)

    events = serializers.ListField(
        child=serializers.CharField(
            help_text=(
                "List of events to subscribe to, "
                "e.g. ['PRICE_UPDATE_AAPL', 'PRICE_UPDATE_GOOGL']."
            )
        ),
        required=True,
        help_text=(
            "Comma-separated list of events "
            "(e.g., 'PRICE_UPDATE_AAPL,PRICE_UPDATE_GOOGL')."
        ),
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

    error = serializers.CharField(help_text="Error message describing what went wrong")


class StatusResponseSerializer(serializers.Serializer):
    """Serializer for status endpoint response"""

    message = serializers.CharField(
        help_text="Status message indicating the application is running"
    )
