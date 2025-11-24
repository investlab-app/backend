import logging
from collections.abc import Iterable
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db import transaction

from modules.investors.models import (
    AccountValueSnapshot,
    Asset,
    Investor,
    NotificationHistory,
)
from modules.investors.schemas import AssetAllocation

logger = logging.getLogger(__name__)


class InvestorStatsService:
    def __init__(self, price_service=None):
        from modules.prices.services import LatestPriceService  # noqa

        self.price_service = price_service or LatestPriceService()

    def get_total_value(self, investor: Investor) -> Decimal:
        total_assets_value = self.get_total_assets_value(investor)
        return total_assets_value + investor.balance

    def get_total_assets_value(self, investor: Investor) -> Decimal:
        assets = Asset.objects.filter(investor=investor)
        tickers = [a.ticker.ticker.upper() for a in assets]
        prices = self.price_service.get_prices_default_dict()
        prices = {ticker: prices[ticker] for ticker in tickers}

        asset_value = Decimal(0)
        for a in assets:
            asset_value += prices[a.ticker.ticker.upper()] * a.volume

        return asset_value

    def get_asset_allocation(self, investor: Investor) -> list[AssetAllocation]:
        assets = Asset.objects.filter(investor=investor)
        tickers = [a.ticker.ticker.upper() for a in assets]
        prices = self.price_service.get_prices_default_dict()
        prices = {ticker: prices[ticker] for ticker in tickers}
        allocations = []

        total_value = 0
        for a in assets:
            total_value += a.volume * prices[a.ticker.ticker.upper()]

        for a in assets:
            ticker = a.ticker.ticker.upper()
            value = a.volume * prices[ticker]
            allocations.append(
                AssetAllocation(
                    asset=a,
                    percentage=(value / total_value * 100) if total_value > 0 else 0,
                    price_per_action=prices[ticker],
                    total_value=a.volume * prices[ticker],
                )
            )

        return allocations


class InvestorValueHistoryService:
    def __init__(
        self,
        stats_service: InvestorStatsService | None = None,
        investors: Iterable[Investor] | None = None
    ):
        self.stats_service = stats_service or InvestorStatsService()
        self.investors = investors or Investor.objects.all()

    def save_for_all_investors(self):
        snapshots = []
        for i in self.investors:
            value = self.stats_service.get_total_value(i)
            snapshots.append(AccountValueSnapshot(investor=i, value=value))

        with transaction.atomic():
            AccountValueSnapshot.objects.bulk_create(snapshots)


class NotificationHistoryService:
    async def save_notification_to_history(
        self,
        investor_id: str,
        notification_type: str,
        message_en: str,
        message_pl: str,
    ) -> None:
        try:
            await sync_to_async(NotificationHistory.objects.create)(
                investor_id=investor_id,
                type=notification_type,
                message_en=message_en,
                message_pl=message_pl,
            )
            logger.debug("Saved notification to history for investor %s", investor_id)
        except Exception as e:
            logger.error("Failed to save notification to history: %s", e)
