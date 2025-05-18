from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class InstrumentPriceSchema(BaseModel):
    timestamp: datetime
    ticker: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
