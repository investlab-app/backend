from django.core.management.base import BaseCommand
from modules.prices.services import LatestPriceService
from time import sleep

class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            prices = LatestPriceService.get_prices()
            print(prices)
            sleep(1)