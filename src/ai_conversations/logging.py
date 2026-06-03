"""Logging configuration for ai-conversations."""

import logging
import sys

from .config import get_config


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure and return the application logger."""
    config = get_config()
    level = logging.DEBUG if verbose else getattr(logging, config.log_level.upper(), logging.INFO)

    logger = logging.getLogger("ai_conversations")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    return logger


def get_logger(name: str = "ai_conversations") -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
