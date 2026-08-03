"""Unit tests for the CLI module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from aifme_scout.cli import main
from aifme_scout.extractors.models import (
    ScoutMeta,
    ScoutSchema,
    ScoutSite,
)
from aifme_scout.scanner.scanner import FetchError, RobotsDisallowedError
from aifme_scout.utils.models import Summary


def _make_schema(target_url: str = "https://example.com") -> ScoutSchema:
    """Create a minimal ScoutSchema for testing."""
    return ScoutSchema(
        meta=ScoutMeta(
            schema_version="1.0.0",
            engine_version="1.0.0-rc2",
            timestamp="2024-01-01T00:00:00+00:00",
        ),
        site=ScoutSite(url=target_url, target_url=target_url),
        seo=[],
        metadata=[],
        technology=[],
        content=[],
        social=[],
        competitors=[],
        evidence=[],
        diagnostics={
            "total_evidence_items": 0,
            "seo_items": 0,
            "metadata_items": 0,
            "technology_items": 0,
            "content_items": 0,
            "social_items": 0,
            "competitor_items": 0,
            "build_timestamp": "2024-01-01T00:00:00+00:00",
        },
    )


def _make_summary() -> Summary:
    """Create a minimal Summary for testing."""
    return Summary(
        text="## Executive Summary\nTarget site: https://example.com\n",
        evidence_refs=[],
    )


class TestCLIHelp:
    """Tests for CLI help and version."""

    def test_help_prints_and_exits(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_version_prints_and_exits(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_no_command_returns_one(self, capsys: pytest.CaptureFixture[str]) -> None:
        result = main([])
        assert result == 1


class TestSuccessfulScan:
    """Tests for successful scan execution."""

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_scan_returns_zero(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.return_value = MagicMock()
        mock_extractors.return_value = (_make_schema(), _make_summary())

        result = main([
            "scan",
            "https://example.com",
            "--out",
            str(tmp_path),
        ])
        assert result == 0

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_json_output_creates_file(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.return_value = MagicMock()
        mock_extractors.return_value = (_make_schema(), _make_summary())

        result = main([
            "scan",
            "https://example.com",
            "--output",
            "json",
            "--out",
            str(tmp_path),
        ])
        assert result == 0
        assert (tmp_path / "scan-result.json").exists()

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_markdown_output_creates_file(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.return_value = MagicMock()
        mock_extractors.return_value = (_make_schema(), _make_summary())

        result = main([
            "scan",
            "https://example.com",
            "--output",
            "markdown",
            "--out",
            str(tmp_path),
        ])
        assert result == 0
        assert (tmp_path / "report.md").exists()

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_both_output_creates_files(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.return_value = MagicMock()
        mock_extractors.return_value = (_make_schema(), _make_summary())

        result = main([
            "scan",
            "https://example.com",
            "--output",
            "both",
            "--out",
            str(tmp_path),
        ])
        assert result == 0
        assert (tmp_path / "scan-result.json").exists()
        assert (tmp_path / "report.md").exists()

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_output_directory_created(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
        tmp_path: Path,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.return_value = MagicMock()
        mock_extractors.return_value = (_make_schema(), _make_summary())

        out_dir = tmp_path / "output"
        result = main([
            "scan",
            "https://example.com",
            "--out",
            str(out_dir),
        ])
        assert result == 0
        assert out_dir.exists()


class TestExitCodes:
    """Tests for exit code handling."""

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_invalid_url_returns_one(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.side_effect = Exception("Invalid URL")
        result = main(["scan", "not-a-url"])
        assert result == 5

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_network_failure_returns_two(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.side_effect = FetchError("Network timeout")
        result = main(["scan", "https://example.com"])
        assert result == 2

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_scanner_failure_returns_three(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.side_effect = RobotsDisallowedError("robots.txt disallows")
        result = main(["scan", "https://example.com"])
        assert result == 3

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_parser_failure_returns_four(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.side_effect = Exception("Parse error")
        result = main(["scan", "https://example.com"])
        assert result == 4

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_internal_error_returns_five(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.return_value = MagicMock()
        mock_extractors.side_effect = Exception("Unexpected error")
        result = main(["scan", "https://example.com"])
        assert result == 5


class TestVerboseQuiet:
    """Tests for verbose and quiet modes."""

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_verbose_mode(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.return_value = MagicMock()
        mock_extractors.return_value = (_make_schema(), _make_summary())

        result = main([
            "scan",
            "https://example.com",
            "--verbose",
        ])
        assert result == 0

    @patch("aifme_scout.cli._run_extractors_and_build")
    @patch("aifme_scout.cli._run_parser")
    @patch("aifme_scout.cli._run_scanner")
    @patch("aifme_scout.cli.resolve")
    def test_quiet_mode(
        self,
        mock_resolve: MagicMock,
        mock_scanner: MagicMock,
        mock_parser: MagicMock,
        mock_extractors: MagicMock,
    ) -> None:
        mock_cfg = MagicMock()
        mock_cfg.max_pages = 25
        mock_cfg.crawl_delay_ms = 1000
        mock_resolve.return_value = mock_cfg
        mock_scanner.return_value = MagicMock(target_url="https://example.com")
        mock_parser.return_value = MagicMock()
        mock_extractors.return_value = (_make_schema(), _make_summary())

        result = main([
            "scan",
            "https://example.com",
            "--quiet",
        ])
        assert result == 0
