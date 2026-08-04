"""Command Line Interface for AIFME Scout OSS."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from aifme_scout.exporters import export_markdown_to_file, export_to_file
from aifme_scout.extractors.models import ScoutSchema
from aifme_scout.parser.models import ParsedSite
from aifme_scout.scanner.models import RawSite
from aifme_scout.utils.config import resolve
from aifme_scout.utils.constants import ScanMode
from aifme_scout.utils.exceptions import ConfigurationError, ScoutError
from aifme_scout.utils.logging import get_logger
from aifme_scout.utils.models import Summary

_LOGGER = get_logger(__name__)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the aifme-scout CLI.

    Args:
        argv: Command-line arguments. Uses sys.argv if not provided.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        prog="aifme-scout",
        description="AIFME Scout OSS - website and marketing intelligence toolkit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    subparsers = parser.add_subparsers(dest="command")

    scan_parser = subparsers.add_parser("scan", help="Scan a website")
    scan_parser.add_argument("url", help="Target URL to scan")
    scan_parser.add_argument(
        "--output",
        choices=["json", "markdown", "both"],
        default="both",
        help="Export format (default: both)",
    )
    scan_parser.add_argument(
        "--out",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)",
    )
    scan_parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    scan_parser.add_argument(
        "--timeout",
        type=float,
        help="Request timeout in seconds",
    )
    scan_parser.add_argument(
        "--user-agent",
        type=str,
        help="Custom User-Agent header",
    )
    scan_parser.add_argument(
        "--mode",
        choices=["no-llm", "llm"],
        default="no-llm",
        help="Summary generation mode (default: no-llm)",
    )
    scan_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    scan_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )

    args = parser.parse_args(argv)

    if args.command == "scan":
        return _run_scan(args)
    if args.command is None:
        parser.print_help()
        return 1

    parser.print_help()
    return 1


def _run_scan(args: argparse.Namespace) -> int:
    """Execute a scan command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code.
    """
    log_level = "WARNING"
    if args.verbose:
        log_level = "DEBUG"
    elif args.quiet:
        log_level = "ERROR"

    logger = get_logger(__name__)
    logger.setLevel(getattr(logging, log_level, logging.WARNING))

    try:
        cfg = resolve(
            output_dir=args.out,
            mode=args.mode,
            config_file=args.config,
            log_level=log_level,
        )
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    scan_mode = ScanMode(args.mode)
    timeout = args.timeout if args.timeout is not None else 10.0
    user_agent = args.user_agent if args.user_agent is not None else "AIFME-Scout-OSS/1.0.0"

    try:
        raw_site = _run_scanner(args.url, cfg, timeout, user_agent)
    except ScoutError as exc:
        _LOGGER.error("Scan failed: %s", exc)
        return _scout_error_to_exit_code(exc)
    except Exception:
        _LOGGER.exception("Unexpected error during scan")
        return 5

    try:
        parsed = _run_parser(raw_site)
    except Exception as exc:
        _LOGGER.error("Parse failed: %s", exc)
        return 4

    try:
        schema, summary = _run_extractors_and_build(raw_site, parsed, scan_mode)
    except ScoutError as exc:
        _LOGGER.error("Extraction failed: %s", exc)
        return 5
    except Exception:
        _LOGGER.exception("Unexpected error during extraction")
        return 5

    output_dir = args.out
    output_dir.mkdir(parents=True, exist_ok=True)

    output_format = args.output
    try:
        if output_format in ("json", "both"):
            export_to_file(schema, output_dir / "scan-result.json")
        if output_format in ("markdown", "both"):
            export_markdown_to_file(summary, output_dir / "report.md")
    except OSError as exc:
        print(f"Write failed: {exc}", file=sys.stderr)
        return 5

    return 0


def _run_scanner(
    url: str,
    cfg: object,
    timeout: float,
    user_agent: str,
) -> RawSite:
    """Run the website scanner.

    Args:
        url: Target URL.
        cfg: Configuration object.
        timeout: Request timeout in seconds.
        user_agent: User-Agent header value.

    Returns:
        RawSite from the scanner.
    """
    from aifme_scout.scanner.scanner import ScanOptions as ScannerScanOptions
    from aifme_scout.scanner.scanner import scan

    options = ScannerScanOptions(
        max_pages=cfg.max_pages if hasattr(cfg, "max_pages") else 25,
        crawl_delay_ms=cfg.crawl_delay_ms if hasattr(cfg, "crawl_delay_ms") else 1000,
        timeout_seconds=timeout,
    )
    return scan(url, options, user_agent=user_agent)


def _run_parser(raw_site: RawSite) -> ParsedSite:
    """Run the HTML parser.

    Args:
        raw_site: RawSite from the scanner.

    Returns:
        ParsedSite from the parser.
    """
    from aifme_scout.parser import parse

    return parse(raw_site)


def _run_extractors_and_build(
    raw_site: RawSite,
    parsed: ParsedSite,
    mode: ScanMode,
) -> tuple[ScoutSchema, Summary]:
    """Run extractors, evidence collection, schema build, and summary.

    Args:
        raw_site: RawSite from the scanner.
        parsed: ParsedSite from the parser.
        mode: Scan mode for summary generation.

    Returns:
        (ScoutSchema, Summary) tuple.
    """
    from aifme_scout.engine.summary import summarize
    from aifme_scout.extractors import (
        build_schema,
        collect_evidence,
        detect_technology,
        discover_social,
        extract_content,
        extract_metadata,
        resolve_competitors,
    )
    from aifme_scout.extractors.seo import analyze

    seo_result = analyze(parsed)
    metadata_result = extract_metadata(parsed)
    technology_result = detect_technology(raw_site, parsed)
    content_result = extract_content(parsed)
    social_result = discover_social(parsed)
    competitor_result = resolve_competitors(parsed)
    evidence_collection = collect_evidence(
        seo_result=seo_result,
        metadata_result=metadata_result,
        technology_result=technology_result,
        content_result=content_result,
        social_result=social_result,
        competitor_result=competitor_result,
        target_url=raw_site.target_url if hasattr(raw_site, "target_url") else "",
    )
    schema = build_schema(evidence_collection)
    summary = summarize(schema, mode=mode)
    return schema, summary


def _scout_error_to_exit_code(error: ScoutError) -> int:
    """Map a ScoutError to an exit code.

    Args:
        error: The exception to map.

    Returns:
        Exit code.
    """
    from aifme_scout.scanner import (
        FetchError,
        InvalidURLError,
        ResponseTooLargeError,
        RobotsDisallowedError,
        SSRFViolationError,
        UnsupportedContentTypeError,
    )

    if isinstance(
        error,
        (InvalidURLError,),
    ):
        return 1
    if isinstance(error, (FetchError,)):
        return 2
    if isinstance(
        error,
        (
            RobotsDisallowedError,
            ResponseTooLargeError,
            UnsupportedContentTypeError,
            SSRFViolationError,
        ),
    ):
        return 3
    return 5
