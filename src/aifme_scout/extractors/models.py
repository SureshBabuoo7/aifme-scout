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


@dataclass(frozen=True)
class ContentElementProvenance:
    """Provenance for an extracted content element."""

    page_url: str
    dom_path: str
    tag: str
    attributes: dict[str, str] = field(default_factory=dict)
    original_text: str | None = None


@dataclass(frozen=True)
class ContentHeading:
    """Extracted heading element."""

    level: int
    text: str
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentParagraph:
    """Extracted paragraph element."""

    text: str
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentListItem:
    """Extracted list item element."""

    text: str
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentList:
    """Extracted list element."""

    list_type: str
    items: list[ContentListItem] = field(default_factory=list)
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentTable:
    """Extracted table element."""

    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentImage:
    """Extracted image element."""

    src: str
    alt: str | None = None
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentLink:
    """Extracted link element."""

    text: str
    href: str
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentButton:
    """Extracted button element."""

    text: str
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentForm:
    """Extracted form element."""

    action: str | None = None
    method: str | None = None
    input_names: list[str] = field(default_factory=list)
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentBreadcrumb:
    """Extracted breadcrumb element."""

    items: list[str] = field(default_factory=list)
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentFooter:
    """Extracted footer content."""

    text: str
    provenance: ContentElementProvenance | None = None


@dataclass(frozen=True)
class ContentPageResult:
    """Content extracted from a single page."""

    url: str
    headings: list[ContentHeading] = field(default_factory=list)
    paragraphs: list[ContentParagraph] = field(default_factory=list)
    lists: list[ContentList] = field(default_factory=list)
    tables: list[ContentTable] = field(default_factory=list)
    images: list[ContentImage] = field(default_factory=list)
    links: list[ContentLink] = field(default_factory=list)
    buttons: list[ContentButton] = field(default_factory=list)
    forms: list[ContentForm] = field(default_factory=list)
    breadcrumbs: list[ContentBreadcrumb] = field(default_factory=list)
    footer: ContentFooter | None = None


@dataclass(frozen=True)
class ContentResult:
    """Complete content extraction result for a site."""

    target_url: str
    pages: list[ContentPageResult] = field(default_factory=list)


@dataclass(frozen=True)
class SocialProfileProvenance:
    """Provenance for a discovered social profile."""

    page_url: str
    dom_path: str
    tag: str
    attribute: str
    original_url: str


@dataclass(frozen=True)
class SocialProfile:
    """Discovered social profile."""

    platform: str
    url: str
    username: str | None = None
    profile_type: str | None = None
    detection_method: str = "link"
    provenance: SocialProfileProvenance | None = None


@dataclass(frozen=True)
class SocialPageResult:
    """Social profiles discovered on a single page."""

    url: str
    profiles: list[SocialProfile] = field(default_factory=list)


@dataclass(frozen=True)
class SocialResult:
    """Complete social discovery result for a site."""

    target_url: str
    pages: list[SocialPageResult] = field(default_factory=list)


@dataclass(frozen=True)
class CompetitorProvenance:
    """Provenance for a discovered competitor."""

    page_url: str
    dom_path: str
    tag: str
    attribute: str
    original_text: str | None = None
    original_url: str | None = None


@dataclass(frozen=True)
class Competitor:
    """Discovered competitor."""

    name: str
    url: str | None = None
    source: str = ""
    discovery_method: str = "USER_SUPPLIED"
    confidence: str = "high"
    evidence: str | None = None
    provenance: CompetitorProvenance | None = None


@dataclass(frozen=True)
class CompetitorPageResult:
    """Competitors discovered on a single page."""

    url: str
    competitors: list[Competitor] = field(default_factory=list)


@dataclass(frozen=True)
class CompetitorResult:
    """Complete competitor discovery result for a site."""

    target_url: str
    pages: list[CompetitorPageResult] = field(default_factory=list)
    user_supplied: list[Competitor] = field(default_factory=list)
    heuristic_discovery_status: str = "DEFERRED"
