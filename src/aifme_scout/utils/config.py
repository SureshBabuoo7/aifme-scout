"""Configuration subsystem.

Resolves runtime configuration with the precedence:
  CLI flags > environment variables > scout.config.yaml > built-in defaults

An invalid configuration value causes a fail-fast ConfigurationError before
any network call or scan work begins.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from aifme_scout.utils.constants import (
    CONFIG_FILE_NAME,
    DEFAULT_CRAWL_DELAY_MS,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_PAGES,
    ScanMode,
)
from aifme_scout.utils.exceptions import ConfigurationError


@dataclass(frozen=True)
class Configuration:
    """Immutable application configuration."""

    output_dir: Path = Path(".")
    mode: ScanMode = ScanMode.NO_LLM
    provider: str | None = None
    crawl_delay_ms: int = DEFAULT_CRAWL_DELAY_MS
    max_pages: int = DEFAULT_MAX_PAGES
    log_level: str = DEFAULT_LOG_LEVEL


def _apply_cli_flags(
    cfg: Configuration,
    output_dir: Path | None = None,
    mode: str | None = None,
    provider: str | None = None,
    crawl_delay_ms: int | None = None,
    max_pages: int | None = None,
    log_level: str | None = None,
) -> Configuration:
    if not any(
        v is not None for v in [output_dir, mode, provider, crawl_delay_ms, max_pages, log_level]
    ):
        return cfg
    return Configuration(
        output_dir=output_dir if output_dir is not None else cfg.output_dir,
        mode=ScanMode(mode) if mode is not None else cfg.mode,
        provider=provider if provider is not None else cfg.provider,
        crawl_delay_ms=crawl_delay_ms if crawl_delay_ms is not None else cfg.crawl_delay_ms,
        max_pages=max_pages if max_pages is not None else cfg.max_pages,
        log_level=log_level if log_level is not None else cfg.log_level,
    )


def _apply_env(cfg: Configuration) -> Configuration:
    updates: dict[str, Any] = {}
    if "SCOUT_OUTPUT_DIR" in os.environ:
        updates["output_dir"] = Path(os.environ["SCOUT_OUTPUT_DIR"])
    if "SCOUT_MODE" in os.environ:
        updates["mode"] = ScanMode(os.environ["SCOUT_MODE"])
    if "SCOUT_PROVIDER" in os.environ:
        updates["provider"] = os.environ["SCOUT_PROVIDER"]
    if "SCOUT_CRAWL_DELAY_MS" in os.environ:
        updates["crawl_delay_ms"] = int(os.environ["SCOUT_CRAWL_DELAY_MS"])
    if "SCOUT_MAX_PAGES" in os.environ:
        updates["max_pages"] = int(os.environ["SCOUT_MAX_PAGES"])
    if "SCOUT_LOG_LEVEL" in os.environ:
        updates["log_level"] = os.environ["SCOUT_LOG_LEVEL"]
    if not updates:
        return cfg
    return Configuration(
        output_dir=updates.get("output_dir", cfg.output_dir),
        mode=updates.get("mode", cfg.mode),
        provider=updates.get("provider", cfg.provider),
        crawl_delay_ms=updates.get("crawl_delay_ms", cfg.crawl_delay_ms),
        max_pages=updates.get("max_pages", cfg.max_pages),
        log_level=updates.get("log_level", cfg.log_level),
    )


def _apply_config_file(cfg: Configuration, config_file: Path) -> Configuration:
    if not config_file.exists():
        return cfg
    try:
        with config_file.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid config file: {exc}") from exc

    updates: dict[str, Any] = {}
    if "output_dir" in data:
        updates["output_dir"] = Path(data["output_dir"])
    if "mode" in data:
        updates["mode"] = ScanMode(data["mode"])
    if "provider" in data:
        updates["provider"] = data["provider"]
    if "crawl_delay_ms" in data:
        updates["crawl_delay_ms"] = int(data["crawl_delay_ms"])
    if "max_pages" in data:
        updates["max_pages"] = int(data["max_pages"])
    if "log_level" in data:
        updates["log_level"] = str(data["log_level"])
    if not updates:
        return cfg
    return Configuration(
        output_dir=updates.get("output_dir", cfg.output_dir),
        mode=updates.get("mode", cfg.mode),
        provider=updates.get("provider", cfg.provider),
        crawl_delay_ms=updates.get("crawl_delay_ms", cfg.crawl_delay_ms),
        max_pages=updates.get("max_pages", cfg.max_pages),
        log_level=updates.get("log_level", cfg.log_level),
    )


def _validate(cfg: Configuration) -> None:
    if cfg.max_pages < 1:
        raise ConfigurationError("max_pages must be >= 1")
    if cfg.crawl_delay_ms < 0:
        raise ConfigurationError("crawl_delay_ms must be >= 0")
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
    if cfg.log_level.upper() not in valid_levels:
        raise ConfigurationError(
            f"Invalid log_level: {cfg.log_level}. Must be one of {sorted(valid_levels)}"
        )


def resolve(
    output_dir: Path | None = None,
    mode: str | None = None,
    provider: str | None = None,
    crawl_delay_ms: int | None = None,
    max_pages: int | None = None,
    log_level: str | None = None,
    config_file: Path | None = None,
) -> Configuration:
    """Resolve the runtime Configuration.

    Precedence: CLI flags > environment variables > config file > defaults.
    """
    cfg = Configuration()
    if config_file is None:
        config_file = Path(CONFIG_FILE_NAME)
    cfg = _apply_config_file(cfg, config_file)
    cfg = _apply_env(cfg)
    cfg = _apply_cli_flags(
        cfg,
        output_dir=output_dir,
        mode=mode,
        provider=provider,
        crawl_delay_ms=crawl_delay_ms,
        max_pages=max_pages,
        log_level=log_level,
    )
    _validate(cfg)
    return cfg
