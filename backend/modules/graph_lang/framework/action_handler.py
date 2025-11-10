from uuid import UUID
from django.db import transaction
from modules.graph_lang.framework.actions import (
    BuySellAmountAction,
    BuySellForPriceAction,
    BuySellPercentAction,
    NotificationAction,
    Action,
)
from modules.orders.services.order_services import MarketOrderService
from modules.investors.models import Investor, Asset
from modules.instruments.models import Instrument
from modules.graph_lang.models import (
    Graph,
    GraphEffect,
    BuySellEffect,
    NotificationEffect,
)


class ActionHandler:
    def __init__(self, order_service: MarketOrderService):
        self._order_service = order_service or MarketOrderService()

    def handle(
        self,
        investor_id: UUID,
        graph_id: UUID,
        action_set: set[Action],
    ):
        for action in action_set:
            if isinstance(action, BuySellAmountAction):
                self._handle_buy_sell_amount(
                    investor_id=investor_id, graph_id=graph_id, action=action
                )

    def _handle_buy_sell_amount(
        self, investor_id: UUID, graph_id: UUID, action: BuySellAmountAction
    ):
        with transaction.atomic():
            graph = Graph.objects.get(id=graph_id)
            investor = Investor.objects.get(id=investor_id)
            instrument = Instrument.objects.get(ticker__iexact=action.ticker)

            result = self._order_service.create(
                investor=investor,
                instrument=instrument,
                volume=action.amount,
                is_buy=action.action == "buy",
            )
            success = result != None

            effect_detail = BuySellEffect.objects.create(
                instrument=instrument,
                is_buy=action.action == "buy",
                amount=action.amount,
            )
            GraphEffect.objects.create(
                graph=graph, success=success, effect=effect_detail
            )
