"""Structured logging for Scout.

Logs never include target-site content by default. A redaction filter
removes URLs from log output unless explicitly disabled.
"""

from __future__ import annotations

import logging
import re
import sys

_URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)


class _UrlRedactionFilter(logging.Filter):
    """Redact URLs from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _URL_PATTERN.sub("[REDACTED]", str(record.msg))
        if record.args:
            record.args = tuple(
                _URL_PATTERN.sub("[REDACTED]", str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
        return True


class ScoutLogger:
    """Singleton-style logger factory."""

    _configured_loggers: dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(cls, name: str = "aifme_scout") -> logging.Logger:
        if name not in cls._configured_loggers:
            logger = logging.getLogger(name)
            if not logger.handlers:
                handler = logging.StreamHandler(sys.stderr)
                formatter = logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                )
                handler.setFormatter(formatter)
                handler.addFilter(_UrlRedactionFilter())
                logger.addHandler(handler)
            logger.setLevel(logging.WARNING)
            cls._configured_loggers[name] = logger
        return cls._configured_loggers[name]


def get_logger(name: str = "aifme_scout") -> logging.Logger:
    """Return a configured Scout logger."""
    return ScoutLogger.get_logger(name)
