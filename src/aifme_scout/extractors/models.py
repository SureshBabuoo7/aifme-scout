"""Data models for the SEO Extractor module."""

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
