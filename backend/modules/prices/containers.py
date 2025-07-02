from dependency_injector import containers, providers

from modules.prices.repositories import YfinanceRepository
from modules.prices.services import PricesService
from modules.sse.services import SSEService


class PricesContainer(containers.DeclarativeContainer):
    yfinance_repository = providers.Singleton(YfinanceRepository)
    prices_service = providers.Singleton(PricesService, repository=yfinance_repository)
    sse_service = providers.Singleton(SSEService)
