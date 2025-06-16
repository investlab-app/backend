import logging
import sys
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

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, logging_config.get("level", "INFO")))

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)  # Keep debug level for development

    # Create formatter using format from config
    formatter = logging.Formatter(logging_config.get("format"))
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
