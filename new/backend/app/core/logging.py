"""
backend/app/core/logging.py

Application-wide logging configuration.
"""

from __future__ import annotations

import logging
import sys


# ---------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def configure_logging() -> None:
    """
    Configure application-wide logging.

    This function is safe to call multiple times because
    force=True replaces existing root logging handlers.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        stream=sys.stdout,
        force=True,
    )


# ---------------------------------------------------------------------
# Logger helper
# ---------------------------------------------------------------------

def get_logger(
    name: str,
) -> logging.Logger:
    """
    Return a logger for the given module.

    Example:

        from backend.app.core.logging import get_logger

        logger = get_logger(__name__)

        logger.info("Application started")
    """

    return logging.getLogger(name)