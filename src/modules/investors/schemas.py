from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from modules.investors.models import Asset


class AssetAllocation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    asset: Asset
    percentage: float
    price_per_action: Decimal
    total_value: Decimal
