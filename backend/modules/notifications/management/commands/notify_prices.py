import asyncio
import logging

from channels.layers import get_channel_layer
from django.core.management.base import BaseCommand

from modules.notifications.container import get_price_alert_handler
from modules.prices.constants import PRICES_CHANNEL_LAYER

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Background listener that consumes price events and sends "
        "notifications to users."
    )

    def handle(self, *args, **options):
        asyncio.run(self.listen_prices())

    async def listen_prices(self):
        layer = get_channel_layer()
        handler = get_price_alert_handler()

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
