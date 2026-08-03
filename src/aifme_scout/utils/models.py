"""Core data models for Scout.

These models represent the conceptual objects defined in the Architecture
specification. They are frozen dataclasses to enforce immutability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aifme_scout.utils.constants import ScanMode


@dataclass(frozen=True)
class Meta:
    """Top-level metadata for a scan result."""

    schema_version: str
    engine_version: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class Technology:
    """Detected technology fingerprint."""

    name: str
    category: str
    confidence: str = "low"


@dataclass(frozen=True)
class SEO:
    """On-page SEO signals."""

    has_title: bool = False
    has_meta_description: bool = False
    heading_structure_valid: bool = False
    has_canonical: bool = False
    has_sitemap: bool = False
    has_robots_txt: bool = False


@dataclass(frozen=True)
class OpenGraph:
    """Open Graph metadata."""

    title: str | None = None
    description: str | None = None
    image: str | None = None
    url: str | None = None
    type: str | None = None


@dataclass(frozen=True)
class TwitterCard:
    """Twitter Card metadata."""

    card: str | None = None
    title: str | None = None
    description: str | None = None
    image: str | None = None


@dataclass(frozen=True)
class SchemaOrg:
    """Schema.org / JSON-LD metadata."""

    type: str | None = None
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class Metadata:
    """Structured head metadata."""

    open_graph: OpenGraph = field(default_factory=OpenGraph)
    twitter_card: TwitterCard = field(default_factory=TwitterCard)
    schema_org: SchemaOrg = field(default_factory=SchemaOrg)
    favicon_url: str | None = None
    language: str | None = None


@dataclass(frozen=True)
class Content:
    """Extracted body content."""

    headline: str | None = None
    body_summary_blocks: list[str] = field(default_factory=list)
    nav_labels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SocialProfile:
    """A discovered social profile link."""

    platform: str
    url: str


@dataclass(frozen=True)
class SocialProfiles:
    """Collection of discovered social profiles."""

    profiles: list[SocialProfile] = field(default_factory=list)


@dataclass(frozen=True)
class Website:
    """A scanned website with all extracted signals."""

    url: str
    seo: SEO = field(default_factory=SEO)
    technology: list[Technology] = field(default_factory=list)
    metadata: Metadata = field(default_factory=Metadata)
    content: Content = field(default_factory=Content)
    social_profiles: SocialProfiles = field(default_factory=SocialProfiles)


@dataclass(frozen=True)
class Evidence:
    """A claim bound to its source and confidence."""

    claim: str
    source_url: str
    confidence: str = "low"
    collected_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )


@dataclass(frozen=True)
class Summary:
    """Descriptive marketing summary."""

    text: str = ""
    evidence_refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Observation:
    """A flagged gap, risk, or signal."""

    type: str  # "gap" | "risk" | "signal"
    description: str = ""
    evidence_ref: str | None = None


@dataclass(frozen=True)
class ScanError:
    """A partial-failure record."""

    code: str
    message: str
    target_url: str | None = None


@dataclass(frozen=True)
class ScanOptions:
    """Options controlling a single scan run."""

    crawl_delay_ms: int = 1000
    max_pages: int = 25
    headless: bool = False
    timeout: float | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class ScanRequest:
    """Input to a single scan invocation."""

    target_url: str
    competitor_urls: list[str] = field(default_factory=list)
    mode: ScanMode = ScanMode.NO_LLM
    options: ScanOptions = field(default_factory=ScanOptions)


@dataclass(frozen=True)
class ScanResult:
    """Complete output of a scan."""

    meta: Meta
    target: Website
    competitors: list[Website] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    summary: Summary = field(default_factory=Summary)
    observations: list[Observation] = field(default_factory=list)
    errors: list[ScanError] = field(default_factory=list)


@dataclass(frozen=True)
class HealthStatus:
    """Health check response."""

    status: str = "ok"
    version: str = "1.0.0-rc2"
