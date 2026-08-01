# Architecture

_Architecture documentation will be completed in EXEC-20._

See the frozen specification:
- [AIFME Scout OSS Architecture v1.0](./AIFME_Scout_OSS_Architecture_v1.0.md)

## Implemented Modules

### Website Scanner (`src/scanner/`)

The Website Scanner fetches website resources safely and deterministically.

**Public interface:**
- `ScannerService.scan(url, options) -> RawSite`
- `scan(url, options) -> RawSite` (synchronous wrapper)

**Data models:**
- `RawPage` — transport metadata for a single fetched page
- `RawSite` — complete scan output
- `RobotsPolicy` — resolved robots.txt rules

**Error hierarchy:**
- `ScannerError` (base)
  - `FetchError`
  - `SSRFViolationError`
  - `RobotsDisallowedError`
  - `ResponseTooLargeError`
  - `UnsupportedContentTypeError`
  - `InvalidURLError`

**Responsibilities:**
- HTTP GET with configurable timeout
- Safe redirect following
- User-Agent header support
- robots.txt awareness
- HTTPS support
- Content-Type validation
- Maximum response size protection
- SSRF protection

### HTML Parser (`src/parser/`)

Converts raw HTML into a deterministic, navigable DOM tree.

**Public interface:**
- `parse(RawSite) -> ParsedSite`

**Data models:**
- `ParsedSite` — parsed site output
- `ParsedPage` — parsed page with root, head, body
- `Element` — navigable DOM element wrapper
- `ParseWarning` — non-fatal parsing warning
- `ParseError` — fatal parse failure

**Responsibilities:**
- Parse HTML with lenient recovery
- Build navigable DOM tree
- Isolate head/body regions
- Character encoding handling
- Malformed HTML recovery

**Deferred by design:**
- Metadata extraction
- Competitor discovery
- Evidence collection
- Summary Builder
- Exporters

### Social Discovery (`src/extractors/social.py`)

Finds linked social profiles from parsed page links.

**Public interface:**
- `discover(ParsedSite) -> SocialResult`

**Data models:**
- `SocialResult` — complete social discovery result
- `SocialPageResult` — per-page discovered profiles
- `SocialProfile` — discovered social profile
- `SocialProfileProvenance` — provenance tracking

**Responsibilities:**
- Platform detection from link URLs
- JSON-LD social link support
- Open Graph reference support
- Header/footer navigation link support
- Relative URL normalization
- Duplicate elimination
- Provenance preservation

**Deferred by design:**
- Competitor Discovery
- Evidence Collector
- Summary Builder
- Exporters
- CLI behavior
- REST API behavior

### Competitor Discovery (`src/extractors/competitors.py`)

Assembles the competitor comparison set from explicit declarations and user-supplied lists.

**Public interface:**
- `resolve(ParsedSite, user_supplied=[]) -> CompetitorResult`

**Data models:**
- `CompetitorResult` — complete competitor discovery result
- `CompetitorPageResult` — per-page discovered competitors
- `Competitor` — discovered competitor
- `CompetitorProvenance` — provenance tracking

**Responsibilities:**
- User-supplied competitor inclusion
- Explicit competitor reference discovery from comparison/alternatives pages
- Partner page link discovery
- Duplicate elimination
- Provenance preservation
- Rule-based confidence assignment

**Deferred by design:**
- Heuristic competitor discovery (EXEC-14)
- Evidence Collector
- Summary Builder
- Exporters
- CLI behavior
- REST API behavior

### SEO Extractor (`src/extractors/seo.py`)

Derives on-page SEO signals from `ParsedSite`.

**Public interface:**
- `analyze(ParsedSite) -> SEOResult`
- `to_simple_seo(SEOResult) -> SEO`

**Data models:**
- `SEOResult` — complete SEO extraction result
- `SEOPageResult` — per-page SEO signals
- `Title`, `MetaDescription`, `CanonicalURL`, `RobotsMeta`
- `HeadingHierarchy`, `Heading`
- `OpenGraphSEO`, `TwitterCardSEO`
- `StructuredDataPresence`, `Indexability`
- `ElementProvenance` — provenance tracking

**Responsibilities:**
- Title extraction
- Meta description extraction
- Canonical URL extraction
- Robots meta extraction
- Hreflang extraction
- Charset detection
- Viewport detection
- Language detection
- Heading hierarchy analysis
- Open Graph SEO tags
- Twitter Card SEO tags
- Structured data presence detection
- Basic indexability flags

**Deferred by design:**
- SEO scoring
- Recommendations
- Ranking
- Competitor Discovery
- Evidence Collector
- Summary Builder
- Exporters
- CLI behavior
- REST API behavior

### Content Extractor (`src/extractors/content.py`)

Pulls structured content from the parsed body region.

**Public interface:**
- `extract(ParsedSite) -> ContentResult`

**Data models:**
- `ContentResult` — complete content extraction result
- `ContentPageResult` — per-page extracted content
- `ContentHeading` — extracted heading element
- `ContentParagraph` — extracted paragraph element
- `ContentList` — extracted list element
- `ContentListItem` — extracted list item element
- `ContentTable` — extracted table element
- `ContentImage` — extracted image element
- `ContentLink` — extracted link element
- `ContentButton` — extracted button element
- `ContentForm` — extracted form element
- `ContentBreadcrumb` — extracted breadcrumb element
- `ContentFooter` — extracted footer content
- `ContentElementProvenance` — provenance tracking

**Responsibilities:**
- Heading extraction (H1–H6)
- Paragraph extraction
- List extraction (ordered and unordered)
- Table extraction
- Image extraction with alt text
- Link extraction with text and destinations
- Button extraction
- Form extraction
- Breadcrumb extraction
- Footer content extraction
- Provenance preservation

**Deferred by design:**
- Social Discovery
- Competitor Discovery
- Evidence Collector
- Summary Builder
- Exporters
- CLI behavior
- REST API behavior

### Technology Detector (`src/extractors/technology.py`)

Identifies the target's technology stack from deterministic evidence.

**Public interface:**
- `detect(RawSite, ParsedSite) -> TechnologyResult`

**Data models:**
- `TechnologyResult` — complete technology detection result
- `TechnologyPageResult` — per-page detected technologies
- `Technology` — detected technology with provenance
- `TechnologyEvidence` — evidence for a detection

**Responsibilities:**
- Framework detection (React, Next.js, Vue, Nuxt, Angular, Svelte)
- CMS detection (WordPress, Drupal, Joomla, Ghost, Shopify, Wix, Squarespace)
- Web server detection (nginx, Apache, IIS)
- Analytics detection (Google Analytics, Google Tag Manager, Plausible, Matomo)
- CSS framework detection (Bootstrap, Tailwind CSS)
- Version extraction where explicitly available
- Rule-based confidence assignment
- Provenance preservation

**Deferred by design:**
- Content Extractor
- Competitor Discovery
- Evidence Collector
- Summary Builder
- Exporters
- CLI behavior
- REST API behavior

### Metadata Extractor (`src/extractors/metadata.py`)

Pulls structured metadata from the parsed head region.

**Public interface:**
- `extract(ParsedSite) -> MetadataResult`

**Data models:**
- `MetadataResult` — complete metadata extraction result
- `MetadataPageResult` — per-page metadata
- `MetaValue` — extracted metadata value with provenance
- `MetaLink` — discovered link with rel/type
- `VerificationTag` — site verification tag
- `ElementProvenance` — provenance tracking

**Responsibilities:**
- Application name extraction
- Generator extraction
- Author extraction
- Publisher extraction
- Copyright extraction
- Theme color extraction
- Color scheme extraction
- Favicon discovery
- Apple touch icon discovery
- Manifest extraction
- RSS/Atom feed discovery
- Alternate link discovery
- Verification tag extraction (Google, Bing, Yandex, Facebook)
- Web app capable flags

**Deferred by design:**
- Technology detection
- Content extraction
- Social discovery
- Competitor discovery
- Evidence collection
- Summary Builder
- Exporters
- CLI behavior
- REST API behavior
