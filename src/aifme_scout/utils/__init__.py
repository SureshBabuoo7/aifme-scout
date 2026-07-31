"""Cross-cutting utilities package."""

from aifme_scout.utils.config import Configuration, resolve
from aifme_scout.utils.exceptions import (
    ArchitectureViolation,
    ConfigurationError,
    ScoutError,
    UnsupportedFeatureError,
    ValidationError,
)
from aifme_scout.utils.logging import get_logger
from aifme_scout.utils.paths import ensure_dir, safe_relative_path
from aifme_scout.utils.validation import is_valid_url, sanitize_text
from aifme_scout.utils.version import Version

__all__ = [
    "ArchitectureViolation",
    "Configuration",
    "ConfigurationError",
    "ScoutError",
    "UnsupportedFeatureError",
    "ValidationError",
    "Version",
    "ensure_dir",
    "get_logger",
    "is_valid_url",
    "resolve",
    "safe_relative_path",
    "sanitize_text",
]
