from pathlib import Path

from dependency_injector import containers, providers

from config.logging import get_logger
from modules.instruments.containers import InstrumentsContainer
from modules.prices.containers import PricesContainer

logger = get_logger(__name__)


class AppContainer(containers.DeclarativeContainer):
    """Application container."""

    config = providers.Configuration()
    config.from_yaml(Path(__file__).parent / "config.yaml")

    instruments_container = providers.Container(InstrumentsContainer, config=config)
    prices_container = providers.Container(PricesContainer)


def setup_container() -> "AppContainer":
    """Set up the application container."""
    container = AppContainer()
    container.wire(
        modules=[
            "modules.instruments.views",
            "modules.instruments.services",
            "modules.instruments.repositories",
            "modules.prices.views",
            "modules.prices.services",
            "modules.prices.repositories",
            "modules.sse.views",
            "modules.sse.sse_consumer_impl",
        ]
    )
    return container
