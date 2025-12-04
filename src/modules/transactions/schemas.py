from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from modules.instruments.models import Instrument
from modules.investors.models import Investor


class TransactionParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    investor: Investor
    instrument: Instrument
    volume: Decimal = Field(gt=0)
    price_per_unit: Decimal = Field(gt=0)
