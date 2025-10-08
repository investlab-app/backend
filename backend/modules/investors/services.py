from decimal import Decimal

from django.db import transaction
from pydantic import BaseModel

from modules.investors.models import AccountValueSnapshot, Asset, Investor
from modules.prices.repositories import PolygonPricesRepository


class AssetAllocation(BaseModel):
    asset: Asset
    percentage: float
    price_per_action: Decimal
    total_value: Decimal

    class Config:
        arbitrary_types_allowed = True


class InvestorStatsService:
    def __init__(self, price_repository=None):
        self.prices = price_repository or PolygonPricesRepository()

    def get_total_value(self, investor: Investor) -> Decimal:
        assets = Asset.objects.filter(investor=investor)
        tickers = [a.ticker.ticker.upper() for a in assets]
        prices = self.prices.get_prices_map(tickers)

        asset_value = 0
        for a in assets:
            asset_value += prices[a.ticker.ticker.upper()].current_price * a.volume

        return investor.balance + asset_value

    def get_asset_allocation(self, investor: Investor) -> list[AssetAllocation]:
        assets = Asset.objects.filter(investor=investor)
        tickers = [a.ticker.ticker.upper() for a in assets]
        prices = self.prices.get_prices_map(tickers)
        allocations = []

        total_value = 0
        for a in assets:
            total_value += a.volume * prices[a.ticker.ticker.upper()].current_price

        for a in assets:
            ticker = a.ticker.ticker.upper()
            value = a.volume * prices[ticker].current_price
            print("value", value)
            print("total_value", total_value)
            allocations.append(
                AssetAllocation(
                    asset=a,
                    percentage=value / total_value * 100,
                    price_per_action=prices[ticker].current_price,
                    total_value=a.volume * prices[ticker].current_price,
                )
            )

        return allocations


class InvestorValueHistoryService:
    def __init__(self, stats_service=None):
        self.stats_service = stats_service or InvestorStatsService()

    def save_all_investors(self):
        investors = Investor.objects.all()

        snapshots = []
        for i in investors:
            value = self.stats_service.get_total_value(i)
            snapshots.append(AccountValueSnapshot(investor=i, value=value))

        with transaction.atomic():
            [s.save() for s in snapshots]
