from modules.prices.repositories import PolygonPricesRepository
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        repo = PolygonPricesRepository()
        repo.get_daily_market_summary()
        