"""Unit tests for the logging subsystem."""

import logging

from aifme_scout.utils.logging import ScoutLogger, get_logger


def test_get_logger_returns_logger() -> None:
    logger = get_logger("test.logger")
    assert isinstance(logger, logging.Logger)


def test_get_logger_same_instance() -> None:
    logger_a = get_logger("test.singleton")
    logger_b = get_logger("test.singleton")
    assert logger_a is logger_b


def test_logger_has_handler() -> None:
    logger = get_logger("test.handler")
    assert len(logger.handlers) >= 1


def test_logger_default_level_is_warning() -> None:
    logger = get_logger("test.level")
    assert logger.level == logging.WARNING


def test_scout_logger_get_logger() -> None:
    logger = ScoutLogger.get_logger("test.scout")
    assert isinstance(logger, logging.Logger)
