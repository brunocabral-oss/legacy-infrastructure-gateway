"""Structured logging setup for LIG."""

import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured logging output with level control."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    format_str = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"

    logging.basicConfig(
        level=level,
        format=format_str,
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
