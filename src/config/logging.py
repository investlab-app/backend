import logging
from pathlib import Path

import tomllib


def load_config() -> dict:
    """Load logging configuration from pyproject.toml."""

    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
            logging_conf = data.get("tool", {}).get("logging")
            if logging_conf:
                return logging_conf
        except Exception:
            pass

    return {}


def setup_logging() -> None:
    """Configure logging for the application using project config."""
    logging_config = load_config()

    logging.basicConfig(
        level=getattr(logging, logging_config.get("level", "INFO")),
        format=logging_config.get("format"),
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
