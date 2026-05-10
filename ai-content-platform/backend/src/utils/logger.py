"""Thin wrapper around loguru so the rest of the app imports `get_logger`."""
from __future__ import annotations

import sys

from loguru import logger

from src.config.settings import settings

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.app_debug else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    _configured = True


def get_logger(name: str = "app"):
    _configure()
    return logger.bind(component=name)
