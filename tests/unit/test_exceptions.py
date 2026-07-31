"""Unit tests for shared exceptions."""

import pytest

from aifme_scout.utils.exceptions import (
    ArchitectureViolation,
    ConfigurationError,
    ScoutError,
    UnsupportedFeatureError,
    ValidationError,
)


def test_scout_error_is_exception() -> None:
    with pytest.raises(ScoutError):
        raise ScoutError("base error")


def test_configuration_error_is_scout_error() -> None:
    with pytest.raises(ScoutError):
        raise ConfigurationError("config error")


def test_validation_error_is_scout_error() -> None:
    with pytest.raises(ScoutError):
        raise ValidationError("validation error")


def test_architecture_violation_is_scout_error() -> None:
    with pytest.raises(ScoutError):
        raise ArchitectureViolation("boundary violation")


def test_unsupported_feature_error_is_scout_error() -> None:
    with pytest.raises(ScoutError):
        raise UnsupportedFeatureError("not supported")


def test_exception_messages() -> None:
    exc = ConfigurationError("invalid max_pages")
    assert str(exc) == "invalid max_pages"
