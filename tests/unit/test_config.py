"""Unit tests for the configuration subsystem."""

from pathlib import Path

import pytest

from aifme_scout.utils.config import (
    Configuration,
    _apply_cli_flags,
    _apply_config_file,
    _apply_env,
    _validate,
    resolve,
)
from aifme_scout.utils.constants import DEFAULT_CRAWL_DELAY_MS, DEFAULT_MAX_PAGES
from aifme_scout.utils.exceptions import ConfigurationError


def test_default_configuration() -> None:
    cfg = Configuration()
    assert cfg.mode.value == "no-llm"
    assert cfg.provider is None
    assert cfg.crawl_delay_ms == DEFAULT_CRAWL_DELAY_MS
    assert cfg.max_pages == DEFAULT_MAX_PAGES
    assert cfg.output_dir == Path(".")


def test_configuration_is_frozen() -> None:
    cfg = Configuration()
    with pytest.raises(AttributeError):
        cfg.max_pages = 10  # type: ignore[misc]


def test_apply_config_file_missing(tmp_path: Path) -> None:
    cfg = Configuration()
    result = _apply_config_file(cfg, tmp_path / "nonexistent.yaml")
    assert result == cfg


def test_apply_config_file_loads_values(tmp_path: Path) -> None:
    config_path = tmp_path / "scout.config.yaml"
    config_path.write_text("mode: llm\nmax_pages: 50\ncrawl_delay_ms: 2000\n", encoding="utf-8")
    cfg = _apply_config_file(Configuration(), config_path)
    assert cfg.mode.value == "llm"
    assert cfg.max_pages == 50
    assert cfg.crawl_delay_ms == 2000


def test_apply_config_file_invalid_yaml(tmp_path: Path) -> None:
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(": invalid", encoding="utf-8")
    with pytest.raises(ConfigurationError):
        _apply_config_file(Configuration(), config_path)


def test_apply_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCOUT_MODE", "llm")
    monkeypatch.setenv("SCOUT_MAX_PAGES", "42")
    cfg = _apply_env(Configuration())
    assert cfg.mode.value == "llm"
    assert cfg.max_pages == 42


def test_apply_cli_flags_override() -> None:
    cfg = _apply_cli_flags(Configuration(), max_pages=10, mode="llm")
    assert cfg.max_pages == 10
    assert cfg.mode.value == "llm"


def test_apply_cli_flags_no_change() -> None:
    cfg = Configuration()
    result = _apply_cli_flags(cfg)
    assert result == cfg


def test_validate_rejects_negative_max_pages() -> None:
    cfg = Configuration(max_pages=0)
    with pytest.raises(ConfigurationError):
        _validate(cfg)


def test_validate_rejects_negative_crawl_delay() -> None:
    cfg = Configuration(crawl_delay_ms=-1)
    with pytest.raises(ConfigurationError):
        _validate(cfg)


def test_validate_rejects_invalid_log_level() -> None:
    cfg = Configuration(log_level="INVALID")
    with pytest.raises(ConfigurationError):
        _validate(cfg)


def test_validate_accepts_valid_config() -> None:
    cfg = Configuration(max_pages=10, crawl_delay_ms=500, log_level="DEBUG")
    _validate(cfg)  # should not raise


def test_resolve_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = tmp_path / "scout.config.yaml"
    config_path.write_text("mode: llm\nmax_pages: 50\n", encoding="utf-8")
    monkeypatch.setenv("SCOUT_MODE", "no-llm")
    monkeypatch.delenv("SCOUT_MAX_PAGES", raising=False)
    cfg = resolve(mode="llm", max_pages=100, config_file=config_path)
    assert cfg.mode.value == "llm"
    assert cfg.max_pages == 100


def test_resolve_fail_fast_on_invalid() -> None:
    with pytest.raises(ConfigurationError):
        resolve(max_pages=0)
