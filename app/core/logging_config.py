"""Structured logging configuration."""

import logging
import sys
from typing import Any

from app.core.config import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    level = logging.DEBUG if settings.debug else logging.INFO

    # JSON-like structure for production; readable for dev
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if settings.environment == "development"
        else '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format))

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)

    # Reduce noise from third-party libs
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING
    )
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if not settings.database_echo else logging.INFO
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)
