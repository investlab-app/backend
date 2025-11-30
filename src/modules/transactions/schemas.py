from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.instruments.models import Instrument
from modules.investors.models import Investor


class TransactionParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    investor: Investor
    instrument: Instrument
    volume: Decimal
    price_per_unit: Decimal
