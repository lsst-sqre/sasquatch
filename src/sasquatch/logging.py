"""Helpers for configuring logging."""

import logging


def configure_logging(level: str | int) -> None:
    """Configure logging."""
    log_format = "%(levelname)s: %(message)s"
    logging.basicConfig(level=level, format=log_format)
