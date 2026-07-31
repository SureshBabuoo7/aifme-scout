"""Validation helpers."""

from urllib.parse import urlparse

from aifme_scout.utils.exceptions import ValidationError


def is_valid_url(url: str) -> bool:
    """Return True if url is a valid HTTP/HTTPS URL."""
    try:
        result = urlparse(url)
        return all(
            [
                result.scheme in ("http", "https"),
                bool(result.netloc),
            ]
        )
    except Exception:
        return False


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to max_length characters."""
    if not isinstance(text, str):
        raise ValidationError(f"Expected str, got {type(text).__name__}")
    return text[:max_length]
