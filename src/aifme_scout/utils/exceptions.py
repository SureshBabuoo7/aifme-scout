"""Shared exceptions for the Scout codebase."""


class ScoutError(Exception):
    """Base exception for all Scout errors."""


class ConfigurationError(ScoutError):
    """Raised when configuration is invalid."""


class ValidationError(ScoutError):
    """Raised when input validation fails."""


class ArchitectureViolation(ScoutError):
    """Raised when an architecture boundary is violated."""


class UnsupportedFeatureError(ScoutError):
    """Raised when a requested feature is not supported in this version."""
