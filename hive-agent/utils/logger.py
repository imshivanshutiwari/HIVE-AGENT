"""Structured logging setup for HIVE-AGENT."""

import logging
import os
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a configured logger with consistent formatting."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level = getattr(
        logging, (level or os.environ.get("LOG_LEVEL", "INFO")).upper(), logging.INFO
    )
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)-30s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
