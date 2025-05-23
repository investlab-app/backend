from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class InstrumentPriceSchema(BaseModel):
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
