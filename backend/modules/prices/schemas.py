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


type PriceUpdateHandler = Callable[[dict[str, float]], None]


class ClientInfo(BaseModel):
    instruments: set[str]
    handler: PriceUpdateHandler | None = None

    @staticmethod
    def empty():
        return ClientInfo(instruments=set(), handler=None)
