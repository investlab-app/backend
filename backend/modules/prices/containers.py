from dependency_injector import containers, providers

from modules.sse.services import SSEService


class PricesContainer(containers.DeclarativeContainer):
    sse_service = providers.Singleton(SSEService)

