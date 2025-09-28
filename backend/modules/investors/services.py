from decimal import Decimal
from pydantic import BaseModel

from modules.prices.repositories import PolygonPricesRepository
from modules.investors.models import Asset, Investor


class AssetAllocation(BaseModel):
    asset: Asset
    percentage: float
    price_per_action: Decimal
    total_value: Decimal

    class Meta:
        allow_arbitrary_types = True


class InvestorStatsService:
    def __init__(self, price_repository=None):
        self.prices = price_repository or PolygonPricesRepository()

    def get_total_value(investor: Investor) -> Decimal:
        assets = Asset.objects.filter(investor=investor)

    def get_asset_allocation(investor: Investor) -> list[AssetAllocation]:
        pass
