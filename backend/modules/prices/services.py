import logging
from typing import Any

from channels.layers import get_channel_layer

from modules.notifications.services import NotificationService
from modules.prices.constants import PRICES_CHANNEL_LAYER

logger = logging.getLogger(__name__)


class PriceAlertHandler:
    def __init__(self, handler: NotificationService = NotificationService()):
        self.handler = handler

    async def handle(
        self,
        prices: dict[str, Any],
    ) -> None:
        pass

    async def _send_notifications(
        self,
        price_alert: PriceAlert,
        prices: dict[str, Any],
        language: str,
    ) -> None:
        pass

    def _get_email_payload(
        self,
        language: str,
        current_price: float,
        alert: PriceAlert,
    ) -> EmailPayload:
        pass

    def _get_push_payload(
        self,
        language: str,
        current_price: float,
        alert: PriceAlert,
    ) -> PushPayload:
        pass

    def _get_websocket_payload(
        self,
        language: str,
        current_price: float,
        alert: PriceAlert,
    ) -> WebSocketPayload:
        pass


class PriceNotificationService:
    def __init__(self, price_alert_handler = PriceAlertHandler()):
        self.handler = price_alert_handler

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