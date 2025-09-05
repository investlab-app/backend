from celery import shared_task

from modules.instruments.services.sync_base_info import SyncInstrumentsBaseInfoService
from modules.instruments.services.sync_detail_info import (
    SyncInstrumentsDetailInfoService,
)
from modules.instruments.services.sync_images import SyncInstrumentsImages


@shared_task
def sync_instruments_base_info():
    service = SyncInstrumentsBaseInfoService()
    result = service.sync_instruments()
    return result


@shared_task
def sync_instruments_detail_info():
    service = SyncInstrumentsDetailInfoService()
    result = service.sync_instruments_details()
    return result


@shared_task
def sync_instruments_images():
    service = SyncInstrumentsImages()
    result = service.sync_instruments_images()
    return result
