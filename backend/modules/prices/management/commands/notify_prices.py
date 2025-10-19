import asyncio
import logging

from django.core.management.base import BaseCommand

from modules.prices.services import PriceNotificationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Background listener that consumes price events and sends "
        "notifications to users."
    )

    def __init__(self):
        self.price_notification_service = PriceNotificationService()

    def handle(self, *args, **options):
        asyncio.run(self.price_notification_service.listen_prices())
