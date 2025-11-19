from decimal import Decimal

from django.db import transaction

from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.orders.models import LimitOrder, MarketOrder, Order
from modules.prices.services import LatestPriceService


class OrderService:
    """Unified service for creating and deleting market and limit orders.

    Provides two creation helpers: `create_market` and `create_limit`, and a
    `delete` method that handles both order detail types and releases blocked
    funds for buy orders.
    """

    def __init__(self, latest_price_service: LatestPriceService | None = None):
        self.latest_price_service = latest_price_service or LatestPriceService()

    def _get_current_price(self, ticker: str) -> Decimal | None:
        prices = self.latest_price_service.get_prices()
        return prices.get(ticker, None)

    @staticmethod
    def _has_enough_funds(investor: Investor, total_cost: Decimal) -> bool:
        free_funds = investor.balance - investor.blocked_funds
        return free_funds >= total_cost

    @staticmethod
    def _has_enough_assets(
        investor: Investor, instrument: Instrument, requested_volume: Decimal
    ) -> bool:
        """Return True if investor has at least requested_volume of instrument"""

        asset = Asset.objects.filter(investor=investor, ticker=instrument).first()
        if not asset:
            return False

        # Compute already-blocked volume by counting existing sell orders
        blocked = Decimal(0)
        orders = Order.objects.filter(investor=investor, ticker=instrument)
        for o in orders:
            detail = o.detail
            if detail is None:
                continue
            if not detail.is_buy:
                remaining = detail.volume - detail.volume_processed
                if remaining > 0:
                    blocked += remaining

        available = asset.volume - blocked
        return available >= requested_volume

    def create_market(
        self,
        investor: Investor,
        instrument: Instrument,
        volume: Decimal,
        *,
        is_buy: bool,
    ) -> Order | None:
        with transaction.atomic():
            if is_buy:
                investor.blocked_funds = Decimal(investor.blocked_funds)
                current_price = self._get_current_price(instrument.ticker)
                if not current_price:
                    return None
                total_cost = current_price * volume
                if not self._has_enough_funds(investor, total_cost):
                    return None

                investor.blocked_funds += total_cost
                investor.save()
            else:
                if not self._has_enough_assets(investor, instrument, volume):
                    return None

                total_cost = Decimal(0)

            detail = MarketOrder.objects.create(
                volume=volume,
                volume_processed=0,
                is_buy=is_buy,
                blocked_funds=total_cost,
            )

            order = Order.objects.create(
                ticker=instrument, investor=investor, detail=detail
            )

        return order

    def create_limit(
        self,
        investor: Investor,
        instrument: Instrument,
        volume: Decimal,
        *,
        is_buy: bool,
        limit_price: Decimal,
    ) -> Order | None:
        with transaction.atomic():
            total_cost = Decimal(0)
            if is_buy:
                total_cost = limit_price * volume
                if not self._has_enough_funds(investor, total_cost):
                    return None

                investor.blocked_funds += total_cost
                investor.save()
            else:
                if not self._has_enough_assets(investor, instrument, volume):
                    return None

            detail = LimitOrder.objects.create(
                volume=volume,
                volume_processed=0,
                is_buy=is_buy,
                limit_price=limit_price,
                blocked_funds=total_cost,
            )

            order = Order.objects.create(
                ticker=instrument, investor=investor, detail=detail
            )

        return order

    def delete(self, order: Order):
        if not order.detail:
            raise ValueError("Cannot delete order with no detail.")

        with transaction.atomic():
            if order.detail.is_buy:
                order.investor.blocked_funds -= order.detail.blocked_funds
                order.investor.save()

            order.detail.delete()
            order.delete()
