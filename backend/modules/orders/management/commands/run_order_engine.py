import asyncio

from django.core.management.base import BaseCommand

from modules.orders.services import RunOrderEngineService


class Command(BaseCommand):
    def handle(self, *args, **options):
        service = RunOrderEngineService()
        asyncio.run(service.run())
