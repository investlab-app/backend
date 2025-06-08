import threading
import uuid

from pydantic import BaseModel, Field
from rest_framework import serializers
from typing_extensions import override

from modules.prices.services import LivePrices

_lock = threading.Lock()
subscriptions: dict[str, int] = {}
clients: dict[uuid.UUID, set[str]] = {}
live_prices = LivePrices()


class SSERequestSerializer(serializers.Serializer):
    @override
    def to_internal_value(self, data):
        symbols = data.get("symbols")
        if isinstance(symbols, str):
            symbols = [s.strip() for s in symbols.split(",") if s.strip()]
        data["symbols"] = symbols
        return super().to_internal_value(data)

    symbols = serializers.ListField(
        child=serializers.CharField(
            help_text="List of stock symbols to subscribe to, e.g. ['AAPL', 'GOOGL']."
        ),
        required=True,
        help_text="Comma-separated list of ticker symbols (e.g., 'AAPL,MSFT,GOOG').",
    )
    connectionId = serializers.UUIDField(
        required=True, help_text="Unique identifier for the SSE connection."
    )


class SSERequestParams(BaseModel):
    symbols: set[str]
    connection_id: uuid.UUID = Field(..., alias="connectionId")

    class ConfigDict:
        populate_by_name = True


def parse_sse_request(data: dict) -> SSERequestParams:
    serializer = SSERequestSerializer(data=data)

    if not serializer.is_valid():
        raise ValueError(f"Invalid SSE request data: {serializer.errors}")

    return SSERequestParams.model_validate(serializer.validated_data)


def subscribe(client_id: uuid.UUID, symbols: set[str]) -> None:
    with _lock:
        for symbol in iter(symbols):
            subscriptions.setdefault(symbol, 0)
            subscriptions[symbol] += 1

        client_symbols = clients.get(client_id, set())
        clients.update({client_id: symbols | client_symbols})

        live_prices.add_instruments(symbols)


def unsubscribe(client_id: uuid.UUID, symbols: set[str]) -> None:
    with _lock:
        for symbol in iter(symbols):
            if subscriptions[symbol] > 1:
                subscriptions[symbol] -= 1
            elif subscriptions[symbol] == 1:
                del subscriptions[symbol]
                live_prices.remove_instruments({symbol})

        client_symbols = clients.get(client_id, set())
        clients.update({client_id: symbols - client_symbols})
