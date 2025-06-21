from dependency_injector import containers, providers

from modules.prices.repositories import YfinanceRepository
from modules.prices.services import LivePricesService, PricesService


class PricesContainer(containers.DeclarativeContainer):
    yfinance_repository = providers.Singleton(YfinanceRepository)
    prices_service = providers.Singleton(PricesService, repository=yfinance_repository)
    live_prices = providers.Singleton(LivePricesService)
