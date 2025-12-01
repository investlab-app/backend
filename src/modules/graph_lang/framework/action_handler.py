from decimal import Decimal
from uuid import UUID

from django.db import transaction

from modules.graph_lang.framework.actions import (
    Action,
    BuySellAmountAction,
    BuySellForPriceAction,
    BuySellPercentAction,
    NotificationAction,
)
from modules.graph_lang.models import (
    BuySellEffect,
    Graph,
    GraphEffect,
    NotificationEffect,
)
from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.notifications.services import (
    EmailPayload,
    NotificationService,
    PushPayload,
)
from modules.orders.services.order_services import OrderService
from modules.prices.services import LatestPriceService


class ActionHandler:
    def __init__(
        self,
        order_service: OrderService | None = None,
        notification_service: NotificationService | None = None,
        latest_price_service: LatestPriceService | None = None,
    ):
        self._order_service = order_service or OrderService()
        self._notification_service = notification_service or NotificationService()
        self._latest_price_service = latest_price_service or LatestPriceService()

    def handle(
        self,
        investor_id: UUID,
        graph_id: UUID,
        action_set: set[Action],
    ):
        graph = Graph.objects.get(id=graph_id)
        investor = Investor.objects.get(id=investor_id)
        for action in action_set:
            if isinstance(action, BuySellAmountAction):
                self._handle_buy_sell_amount(
                    investor=investor, graph=graph, action=action
                )
            if isinstance(action, BuySellForPriceAction):
                self._handle_buy_sell_price(
                    investor=investor, graph=graph, action=action
                )
            if isinstance(action, BuySellPercentAction):
                self._handle_buy_sell_percentage_of_assets(
                    investor=investor, graph=graph, action=action
                )
            if isinstance(action, NotificationAction):
                self._handle_notification(investor=investor, graph=graph, action=action)

    def _handle_buy_sell_amount(
        self,
        investor: Investor,
        graph: Graph,
        action: BuySellAmountAction,
    ):
        self._try_create_market_order(
            investor=investor,
            graph=graph,
            volume=action.amount,
            is_buy=action.action == "buy",
            ticker=action.ticker,
        )

    def _handle_buy_sell_price(
        self, investor: Investor, graph: Graph, action: BuySellForPriceAction
    ):
        prices = self._latest_price_service.get_prices()
        volume = action.price / prices[action.ticker]
        self._try_create_market_order(
            investor=investor,
            graph=graph,
            volume=volume,
            is_buy=action.action == "buy",
            ticker=action.ticker,
        )

    def _handle_buy_sell_percentage_of_assets(
        self, investor: Investor, graph: Graph, action: BuySellPercentAction
    ):
        if action.percent < 0 or action.percent > 1:
            volume = 0
        else:
            try:
                asset = Asset.objects.get(
                    investor=investor, ticker__ticker__iexact=action.ticker
                )
                volume = asset.volume * action.percent
            except Exception:
                volume = 0

        self._try_create_market_order(
            investor=investor,
            graph=graph,
            volume=volume,
            is_buy=action.action == "buy",
            ticker=action.ticker,
        )

    def _try_create_market_order(
        self,
        investor: Investor,
        graph: Graph,
        volume: Decimal,
        ticker: str,
        *,
        is_buy: bool,
    ):
        action_price = self._latest_price_service.get_prices().get(
            ticker.upper(), Decimal(0)
        )
        with transaction.atomic():
            instrument = Instrument.objects.get(ticker__iexact=ticker)

            if volume > 0:
                result_order, _err = self._order_service.create_market(
                    investor=investor,
                    instrument=instrument,
                    volume=volume,
                    is_buy=is_buy,
                )
                success = result_order is not None
            else:
                volume = Decimal(0)
                success = False

            effect_detail = BuySellEffect.objects.create(
                instrument=instrument,
                is_buy=is_buy,
                amount=volume,
                action_price=action_price,
            )
            GraphEffect.objects.create(
                graph=graph, success=success, effect=effect_detail
            )

    def _handle_notification(
        self, investor: Investor, graph: Graph, action: NotificationAction
    ):
        if action.format == "email":
            payload = EmailPayload(
                subject="Notification from graph", body=action.message
            )
            success = self._notification_service.sync_send_email_notification(
                investor=investor, email_payload=payload
            )
            format_ = NotificationEffect.MAIL
        else:
            payload = PushPayload(title="Notification from graph", body=action.message)
            success = self._notification_service.sync_send_push_notifications(
                investor=investor, push_payload=payload
            )
            format_ = NotificationEffect.PUSH

        with transaction.atomic():
            effect_detail = NotificationEffect.objects.create(
                format=format_, message=action.message
            )
            GraphEffect.objects.create(
                graph=graph, success=success, effect=effect_detail
            )


#  TODO what happens if there is no latest price for ticker? Should fail, implement
