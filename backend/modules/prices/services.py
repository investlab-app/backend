import asyncio
import logging
from typing import Any

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.db.models import Q

from modules.investors.services import NotificationHistoryService
from modules.notifications.services import (
    EmailPayload,
    NotificationService,
    PushPayload,
    WebSocketPayload,
)
from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.prices.models import PriceAlert

logger = logging.getLogger(__name__)


class PriceAlertHandler:
    def __init__(
        self,
        notification_service: NotificationService | None = None,
        notification_history_service: NotificationHistoryService | None = None,
    ):
        self.notification_service = notification_service or NotificationService()
        self.notification_history_service = NotificationHistoryService()

    async def handle(
        self,
        prices: dict[str, Any],
    ) -> None:
        conditions = Q()

        for ticker, price_info in prices.items():
            current_price = price_info.get("close")
            if current_price is None:
                continue

            ticker_conditions = Q(
                instrument__ticker=ticker,
                threshold_type="above",
                threshold_value__lte=current_price,
            ) | Q(
                instrument__ticker=ticker,
                threshold_type="below",
                threshold_value__gte=current_price,
            )

            conditions |= ticker_conditions

        if not conditions.children:
            return

        query = PriceAlert.objects.filter(
            conditions,
            notification_config__is_active=True,
        ).select_related(
            "instrument",
            "investor",
            "notification_config",
        )

        notifications = await sync_to_async(list)(query)

        # concurrency limit
        semaphore = asyncio.Semaphore(10)

        async def process_notification(notification):
            async with semaphore:
                language = notification.investor.language
                await self.send_notifications(notification, prices, language)
                await sync_to_async(notification.delete)()

        tasks = [
            asyncio.create_task(process_notification(notification))
            for notification in notifications
        ]
        await asyncio.gather(*tasks)

    async def send_notifications(
        self,
        price_alert: PriceAlert,
        prices: dict[str, Any],
        language: str,
    ) -> None:
        try:
            price_info = prices[price_alert.instrument.ticker]
            current_price = price_info["close"]

            if price_alert.notification_config.is_email:
                email_payload = self.get_email_payload(
                    language,
                    price_alert.instrument.ticker,
                    current_price,
                    price_alert,
                )
                await self.notification_service.send_email_notification(
                    price_alert.investor,
                    email_payload,
                )

            if price_alert.notification_config.is_push:
                push_payload = self.get_push_payload(
                    language,
                    price_alert.instrument.ticker,
                    current_price,
                    price_alert,
                )
                await self.notification_service.send_push_notifications(
                    price_alert.investor,
                    push_payload,
                )

            if price_alert.notification_config.is_websocket:
                websocket_payload = self.get_websocket_payload(
                    language,
                    price_alert.instrument.ticker,
                    current_price,
                    price_alert,
                )
                await self.notification_service.send_websocket_notifications(
                    price_alert.investor,
                    websocket_payload,
                )

            if any(
                [
                    price_alert.notification_config.is_email,
                    price_alert.notification_config.is_push,
                    price_alert.notification_config.is_websocket,
                ]
            ):
                threshold_type = (
                    "powyżej" if price_alert.threshold_type == "above" else "poniżej"
                )
                message_pl = (
                    f"Twój alert dla {price_alert.instrument.ticker} "
                    f"został wyzwolony. Cena jest teraz "
                    f"{threshold_type} {price_alert.threshold_value}. "
                    f"Aktualna cena: {current_price}"
                )

                message_en = (
                    f"Your alert for {price_alert.instrument.ticker} "
                    f"has been triggered. The price is now "
                    f"{price_alert.threshold_type} {price_alert.threshold_value}. "
                    f"Current price: {current_price}"
                )

                await self.notification_history_service.save_notification_to_history(
                    investor_id=price_alert.investor.id,
                    notification_type="price_alert",
                    message_en=message_en,
                    message_pl=message_pl,
                )
        except Exception as e:
            logger.error("Error handling notification %s: %s", price_alert.id, e)

    def get_email_payload(
        self,
        language: str,
        ticker: str,
        current_price: float,
        notification: PriceAlert,
    ) -> EmailPayload:
        if language == "pl":
            threshold_type = (
                "powyżej" if notification.threshold_type == "above" else "poniżej"
            )
            return EmailPayload(
                subject="Alert cenowy",
                body=(
                    f"Twój alert dla {ticker}. "
                    f"został wyzwolony. Cena jest teraz "
                    f"{threshold_type} {notification.threshold_value}. "
                    f"Aktualna cena: {current_price}"
                ),
            )
        return EmailPayload(
            subject="Price Alert",
            body=(
                f"Your alert for {ticker}. The price is now "
                f"{notification.threshold_type} {notification.threshold_value}. "
                f"Current price: {current_price}"
            ),
        )

    def get_push_payload(
        self,
        language: str,
        ticker: str,
        current_price: float,
        notification: PriceAlert,
    ) -> PushPayload:
        if language == "pl":
            threshold_type = (
                "powyżej" if notification.threshold_type == "above" else "poniżej"
            )
            return PushPayload(
                title="Alert cenowy",
                body=(
                    f"Twój alert dla {ticker} "
                    f"został wyzwolony. Cena jest teraz "
                    f"{threshold_type} {notification.threshold_value}. "
                    f"Aktualna cena: {current_price}"
                ),
            )
        return PushPayload(
            title="Price Alert",
            body=(
                f"Your alert for {ticker} "
                f"has been triggered. The price is now "
                f"{notification.threshold_type} {notification.threshold_value}. "
                f"Current price: {current_price}"
            ),
        )

    def get_websocket_payload(
        self,
        language: str,
        ticker: str,
        current_price: float,
        notification: PriceAlert,
    ) -> WebSocketPayload:
        if language == "pl":
            threshold_type = (
                "powyżej" if notification.threshold_type == "above" else "poniżej"
            )
            return WebSocketPayload(
                message={
                    "type": "price_alert",
                    "title": "Alert cenowy",
                    "body": (
                        f"Twój alert dla {ticker} "
                        f"został wyzwolony. Cena jest teraz "
                        f"{threshold_type} {notification.threshold_value}. "
                        f"Aktualna cena: {current_price}"
                    ),
                }
            )
        return WebSocketPayload(
            message={
                "type": "price_alert",
                "title": "Price Alert",
                "body": (
                    f"Your alert for {ticker} "
                    f"has been triggered. The price is now "
                    f"{notification.threshold_type} {notification.threshold_value}. "
                    f"Current price: {current_price}"
                ),
            }
        )


class PriceNotificationService:
    def __init__(self, price_alert_handler: PriceAlertHandler | None = None):
        self.handler = price_alert_handler or PriceAlertHandler()

    async def listen_prices(self):
        layer = get_channel_layer()
        handler = self.handler

        channel_name = await layer.new_channel()
        await layer.group_add(PRICES_CHANNEL_LAYER, channel_name)
        logger.info("notify_prices worker joined group %s", PRICES_CHANNEL_LAYER)

        try:
            while True:
                try:
                    event = await layer.receive(channel_name)
                    data = event.get("data")

                    if not data:
                        continue

                    await handler.handle(prices=data)
                    logger.debug("Queued price alert handling for %d prices", len(data))
                except Exception as e:
                    logger.exception("Error while processing price alert event: %s", e)

        finally:
            await layer.group_discard(PRICES_CHANNEL_LAYER, channel_name)
            logger.info("notify_prices worker left group %s", PRICES_CHANNEL_LAYER)
