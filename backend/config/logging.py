import logging
from pathlib import Path

import yaml


def load_config() -> dict:
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open("r") as f:
        return yaml.safe_load(f)


def setup_logging() -> None:
    """Configure logging for the application using config.yaml settings."""
    config = load_config()
    logging_config = config.get("logging", {})

    logging.basicConfig(
        level=getattr(logging, logging_config.get("level", "INFO")),
        format=logging_config.get("format"),
    )

    # Set yfinance logger to only show WARNING and above
    logging.getLogger("modules.prices.live_prices_service").setLevel(logging.DEBUG)
    # logging.getLogger("modules.sse.sse_consumer_impl").setLevel(logging.DEBUG)
    # logging.getLogger("modules.prices.live_prices_service").setLevel(logging.DEBUG)
    logging.getLogger("django.request").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("websockets.client").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("daphne.http_protocol").setLevel(logging.WARNING)
    logging.getLogger("daphne.server").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
