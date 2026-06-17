"""Shared logging setup for pipeline scripts and modules."""

import logging
import sys


def configure_logging(verbose: bool = False) -> None:
    """Configure root logging handlers and format once per process."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger for the caller module."""
    return logging.getLogger(name)
