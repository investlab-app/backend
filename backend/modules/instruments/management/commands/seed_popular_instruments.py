import logging

from django.core.management.base import BaseCommand

from modules.core.management.mixins import CommandMessagesMixin
from modules.instruments.management.constants import POPULAR_TICKERS
from modules.instruments.models import Instrument
from modules.instruments.services.sync_base_info import SyncInstrumentsBaseInfoService
from modules.instruments.services.sync_detail_info import (
    SyncInstrumentsDetailInfoService,
)
from modules.instruments.services.sync_images import SyncInstrumentsImages

logger = logging.getLogger(__name__)


class Command(CommandMessagesMixin, BaseCommand):
    def handle(self, *args, **options):
        logger.info("Seeding popular instruments...")

        base_info_service = SyncInstrumentsBaseInfoService(tickers=POPULAR_TICKERS)
        base_info_result = base_info_service.sync_instruments()
        self.print_success("SyncInstrumentsBaseInfoService executed")
        self.print_warning(str(base_info_result) + "\n")

        instruments = Instrument.objects.filter(ticker__in=POPULAR_TICKERS)
        detail_info_service = SyncInstrumentsDetailInfoService(instruments=instruments)
        detail_info_result = detail_info_service.sync_instruments_details()
        self.print_success("SyncInstrumentsDetailInfoService executed")
        self.print_warning(str(detail_info_result) + "\n")

        images_service = SyncInstrumentsImages(instruments=instruments)
        images_result = images_service.sync_instruments_images()
        self.print_success("SyncInstrumentsImages executed")
        self.print_warning(str(images_result) + "\n")

        logger.info("Seeding popular instruments completed.")
        self.print_success("Seeding popular instruments completed.")
