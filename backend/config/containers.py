from pathlib import Path

from dependency_injector import containers, providers

from config.logging import get_logger
from modules.instruments.containers import InstrumentsContainer
from modules.prices.containers import PricesContainer

logger = get_logger(__name__)


class AppContainer(containers.DeclarativeContainer):
    """Application container."""

    config = providers.Configuration()
    try:
        config.from_yaml(Path(__file__).parent / "config.yaml")
    except FileNotFoundError as exc:
        logger.error("Application configuration missing: %s", exc)
        raise

    wiring_config = containers.WiringConfiguration(
        modules=[
            "modules.instruments.views",
            "modules.prices.views",
            "modules.sse.views",
        ]
    )

    instruments_container = providers.Container(InstrumentsContainer, config=config)
    prices_container = providers.Container(PricesContainer)
