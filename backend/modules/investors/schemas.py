from decimal import Decimal

from pydantic import BaseModel

from modules.investors.models import Asset


class AssetAllocation(BaseModel):
    asset: Asset
    percentage: float
    price_per_action: Decimal
    total_value: Decimal

    class Config:
        arbitrary_types_allowed = True
