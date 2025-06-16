from dependency_injector import containers, providers

from modules.instruments.repositories import InstrumentsRepository
from modules.instruments.services import InstrumentsService


class InstrumentsContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    instruments_repository = providers.Singleton(
        InstrumentsRepository, available_instruments=config.instruments.available
    )
    instruments_service = providers.Singleton(
        InstrumentsService, repository=instruments_repository
    )
