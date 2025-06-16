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


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
