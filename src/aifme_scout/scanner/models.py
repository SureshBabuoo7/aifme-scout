"""Data models for the Website Scanner module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aifme_scout.utils.models import ScanError


@dataclass(frozen=True)
class RawPage:
    """A single fetched page with transport-level metadata only."""

    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    html: str
    content_type: str | None = None
    encoding: str | None = None
    response_size_bytes: int = 0
    response_time_ms: float = 0.0
    fetched_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    content_encoding: str | None = None
    is_anti_bot_challenge: bool = False
    is_rate_limited: bool = False
    is_xml: bool = False
    xml_type: str | None = None


@dataclass(frozen=False)
class RobotsPolicy:
    """Resolved robots.txt policy for a target."""

    user_agent: str = "*"
    crawl_delay_ms: int = 1000
    allowed_paths: list[str] = field(default_factory=list)
    disallowed_paths: list[str] = field(default_factory=list)
    raw_content: str | None = None
    sitemap_urls: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RawSite:
    """Raw website output from the scanner.

    Contains only transport-level information. No parsing, extraction,
    or interpretation is performed at this layer.
    """

    target_url: str
    pages: list[RawPage]
    sitemap_urls: list[str]
    robots_policy: RobotsPolicy | None = None
    crawl_depth: int = 0
    errors: list[ScanError] = field(default_factory=list)
    scan_started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    scan_completed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    sitemap_pages_found: int = 0
