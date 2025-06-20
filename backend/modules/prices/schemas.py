import uuid
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class InstrumentPriceSchema(BaseModel):
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal


type HandlerFn = Callable[[dict[str, float]], None]
type ClientId = uuid.UUID
type TickerId = str


class Client(BaseModel):
    tickers: set[TickerId]
    handler: HandlerFn | None = None

    @staticmethod
    def empty() -> "Client":
        return Client(tickers=set(), handler=None)
