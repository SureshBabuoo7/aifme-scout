"""Data models for the extractor modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class ElementProvenance:
    """Provenance for an extracted value."""

    page_url: str
    tag: str
    attribute: str | None = None
    text_snippet: str | None = None


@dataclass(frozen=True)
class Title:
    """Extracted page title."""

    value: str | None
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class MetaDescription:
    """Extracted meta description."""

    value: str | None
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class CanonicalURL:
    """Extracted canonical URL."""

    value: str | None
    provenance: ElementProvenance | None = None
    valid: bool = True


@dataclass(frozen=True)
class RobotsMeta:
    """Extracted robots meta tag."""

    value: str | None
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class Heading:
    """A single heading element."""

    level: int
    text: str
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class HeadingHierarchy:
    """Heading structure for a page."""

    headings: list[Heading] = field(default_factory=list)
    valid: bool = True
    has_h1: bool = False
    duplicate_h1_count: int = 0


@dataclass(frozen=True)
class OpenGraphSEO:
    """Open Graph tags relevant to SEO."""

    title: str | None = None
    description: str | None = None
    url: str | None = None
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class TwitterCardSEO:
    """Twitter Card tags relevant to SEO."""

    title: str | None = None
    description: str | None = None
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class StructuredDataPresence:
    """Whether structured data was detected."""

    has_json_ld: bool = False
    has_microdata: bool = False
    has_rdfa: bool = False
    count: int = 0


@dataclass(frozen=True)
class Indexability:
    """Basic indexability indicators."""

    noindex: bool = False
    nofollow: bool = False
    noarchive: bool = False
    nosnippet: bool = False


@dataclass(frozen=True)
class SEOPageResult:
    """SEO signals extracted from a single page."""

    url: str
    title: Title | None = None
    meta_description: MetaDescription | None = None
    canonical: CanonicalURL | None = None
    robots: RobotsMeta | None = None
    hreflang: list[str] = field(default_factory=list)
    charset: str | None = None
    viewport: str | None = None
    language: str | None = None
    heading_hierarchy: HeadingHierarchy = field(default_factory=HeadingHierarchy)
    open_graph: OpenGraphSEO = field(default_factory=OpenGraphSEO)
    twitter_card: TwitterCardSEO = field(default_factory=TwitterCardSEO)
    structured_data: StructuredDataPresence = field(default_factory=StructuredDataPresence)
    indexability: Indexability = field(default_factory=Indexability)


@dataclass(frozen=True)
class SEOResult:
    """Complete SEO extraction result for a site."""

    target_url: str
    pages: list[SEOPageResult] = field(default_factory=list)


@dataclass(frozen=True)
class MetaValue:
    """Extracted metadata value with provenance."""

    value: str | None
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class MetaLink:
    """Discovered link with rel/type."""

    url: str
    rel: str | None = None
    type_: str | None = None
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class VerificationTag:
    """Site verification tag."""

    platform: str
    value: str
    provenance: ElementProvenance | None = None


@dataclass(frozen=True)
class MetadataPageResult:
    """Metadata extracted from a single page."""

    url: str
    site_name: MetaValue | None = None
    application_name: MetaValue | None = None
    generator: MetaValue | None = None
    author: MetaValue | None = None
    publisher: MetaValue | None = None
    copyright: MetaValue | None = None
    theme_color: MetaValue | None = None
    color_scheme: MetaValue | None = None
    favicons: list[MetaLink] = field(default_factory=list)
    apple_touch_icons: list[MetaLink] = field(default_factory=list)
    manifest: MetaValue | None = None
    rss_feeds: list[MetaLink] = field(default_factory=list)
    atom_feeds: list[MetaLink] = field(default_factory=list)
    alternate_links: list[MetaLink] = field(default_factory=list)
    verification_tags: list[VerificationTag] = field(default_factory=list)
    web_app_capable: bool = False
    mobile_web_app_capable: bool = False


@dataclass(frozen=True)
class MetadataResult:
    """Complete metadata extraction result for a site."""

    target_url: str
    pages: list[MetadataPageResult] = field(default_factory=list)


@dataclass(frozen=True)
class TechnologyEvidence:
    """Evidence for a detected technology."""

    page_url: str
    detection_rule: str
    matched_value: str
    source: str


@dataclass(frozen=True)
class Technology:
    """Detected technology."""

    name: str
    category: str
    version: str | None = None
    confidence: str = "medium"
    detection_method: str = "fingerprint"
    evidence: list[TechnologyEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class TechnologyPageResult:
    """Technologies detected on a single page."""

    url: str
    technologies: list[Technology] = field(default_factory=list)


@dataclass(frozen=True)
class TechnologyResult:
    """Complete technology detection result for a site."""

    target_url: str
    pages: list[TechnologyPageResult] = field(default_factory=list)
