from decimal import Decimal

from django.db import transaction

from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.orders.models import MarketOrder, Order
from modules.prices.repositories import PolygonPricesRepository


class MarketOrderService:
    def __init__(self, price_repository: PolygonPricesRepository | None = None):
        self.price_repository = price_repository or PolygonPricesRepository()

    def _get_current_price(self, ticker: str) -> Decimal:
        price_summary = self.price_repository.get_price(ticker)
        if not price_summary:
            raise ValueError("Cannot fetch price for the given instrument.")

        return price_summary.current_price

    def _has_enough_funds(
        self,
        investor: Investor,
        instrument: Instrument,
        volume: Decimal,
    ) -> tuple[bool, Decimal]:
        current_price = self._get_current_price(instrument.ticker)
        total_cost = current_price * volume
        needed_money = investor.balance - investor.blocked_funds
        return needed_money >= total_cost, current_price * volume

    def create(
        self,
        investor: Investor,
        instrument: Instrument,
        volume: Decimal,
        *,
        is_buy: bool,
    ) -> Order | None:
        with transaction.atomic():
            if is_buy:
                has_enough_funds, total_cost = self._has_enough_funds(
                    investor, instrument, volume
                )
                if not has_enough_funds:
                    return None

                investor.blocked_funds += total_cost
                investor.save()

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

    def delete(self, order: Order):
        if not isinstance(order.detail, MarketOrder):
            raise ValueError("Only market orders can be deleted with this service.")

        with transaction.atomic():
            if order.detail.is_buy:
                order.investor.blocked_funds -= order.detail.blocked_funds
                order.investor.save()

            order.detail.delete()
            order.delete()
