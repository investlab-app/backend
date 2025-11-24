from decimal import Decimal

from pydantic import BaseModel

from modules.instruments.models import Instrument
from modules.investors.models import Investor


class TransactionParams(BaseModel):
    investor: Investor
    ticker: Instrument
    volume: Decimal
    action_price: Decimal

    class Config:
        arbitrary_types_allowed = True
