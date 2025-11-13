from decimal import Decimal

from django.db import transaction

from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.orders.models import LimitOrder, MarketOrder, Order
from modules.prices.repositories import PolygonPricesRepository


class OrderService:
    """Unified service for creating and deleting market and limit orders.

    Provides two creation helpers: `create_market` and `create_limit`, and a
    `delete` method that handles both order detail types and releases blocked
    funds for buy orders.
    """

    def __init__(self, price_repository: PolygonPricesRepository | None = None):
        self.price_repository = price_repository or PolygonPricesRepository()

    def _get_current_price(self, ticker: str) -> Decimal:
        price_summary = self.price_repository.get_price(ticker)
        if not price_summary:
            raise ValueError("Cannot fetch price for the given instrument.")

        return price_summary.current_price

    @staticmethod
    def _has_enough_funds(investor: Investor, total_cost: Decimal) -> bool:
        free_funds = investor.balance - investor.blocked_funds
        return free_funds >= total_cost

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
                current_price = self._get_current_price(instrument.ticker)
                total_cost = current_price * volume
                if not self._has_enough_funds(investor, total_cost):
                    return None

                investor.blocked_funds += total_cost
                investor.save()
            else:
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
        with transaction.atomic():
            if order.detail is None:
                raise ValueError("Order detail cannot be None")

            if order.detail.is_buy:
                order.investor.blocked_funds -= order.detail.blocked_funds
                order.investor.save()

            order.detail.delete()
            order.delete()
