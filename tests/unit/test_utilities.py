"""Unit tests for shared utilities."""

from pathlib import Path

import pytest

from aifme_scout.utils.exceptions import ValidationError
from aifme_scout.utils.paths import ensure_dir, safe_relative_path
from aifme_scout.utils.validation import is_valid_url, sanitize_text
from aifme_scout.utils.version import Version


class TestVersion:
    def test_from_string_valid(self) -> None:
        v = Version.from_string("2.3.4")
        assert str(v) == "2.3.4"

    def test_from_string_invalid(self) -> None:
        with pytest.raises(ValueError):
            Version.from_string("bad")

    def test_from_string_non_numeric(self) -> None:
        with pytest.raises(ValueError):
            Version.from_string("a.b.c")


class TestPaths:
    def test_ensure_dir_creates_directory(self, tmp_path: Path) -> None:
        target = tmp_path / "a" / "b" / "c"
        result = ensure_dir(target)
        assert result.exists()
        assert result.is_dir()

    def test_ensure_dir_existing(self, tmp_path: Path) -> None:
        result = ensure_dir(tmp_path)
        assert result == tmp_path

    def test_safe_relative_path_within_base(self, tmp_path: Path) -> None:
        target = tmp_path / "file.txt"
        rel = safe_relative_path(tmp_path, target)
        assert rel == Path("file.txt")

    def test_safe_relative_path_outside_base(self, tmp_path: Path) -> None:
        target = Path("/outside/base/file.txt")
        rel = safe_relative_path(tmp_path, target)
        assert rel == target


class TestValidation:
    def test_is_valid_url_https(self) -> None:
        assert is_valid_url("https://example.com") is True

    def test_is_valid_url_http(self) -> None:
        assert is_valid_url("http://example.com") is True

    def test_is_valid_url_missing_scheme(self) -> None:
        assert is_valid_url("example.com") is False

    def test_is_valid_url_empty(self) -> None:
        assert is_valid_url("") is False

    def test_sanitize_text_short(self) -> None:
        assert sanitize_text("hello") == "hello"

    def test_sanitize_text_truncates(self) -> None:
        text = "a" * 2000
        result = sanitize_text(text, max_length=10)
        assert len(result) == 10

    def test_sanitize_text_non_string_raises(self) -> None:
        with pytest.raises(ValidationError):
            sanitize_text(123)  # type: ignore[arg-type]
