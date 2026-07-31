"""Path helpers."""

from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_relative_path(base: Path, target: Path) -> Path:
    """Compute a relative path safely, falling back to the absolute path."""
    try:
        return target.relative_to(base)
    except ValueError:
        return target
