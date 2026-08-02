# Architecture

This document describes the implemented modules in AIFME Scout OSS.

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
- Summary Builder
- Exporters

### Evidence Collector (`src/extractors/evidence.py`)

Normalizes extractor outputs into a common evidence model.

**Public interface:**
- `collect(seo_result, metadata_result, technology_result, content_result, social_result, competitor_result, target_url) -> EvidenceCollection`

**Data models:**
- `EvidenceCollection` — complete evidence collection for a site
- `EvidenceItem` — normalized evidence item from any extractor
- `EvidenceProvenance` — unified provenance for an evidence item

**Responsibilities:**
- Evidence normalization from all extractors
- Evidence ID generation
- Deterministic ordering
- Duplicate elimination
- Provenance preservation
- Confidence preservation from upstream extractors

**Deferred by design:**
- Schema Builder
- Summary Builder
- CLI behavior
- REST API behavior

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
- REST API behavior

### Command Line Interface (`src/cli/__init__.py`)

The CLI is the orchestration layer for Scout OSS. It executes the complete
pipeline by calling existing modules in sequence.

**Public interface:**
- `main(argv: list[str] | None = None) -> int`

**Responsibilities:**
- Parse CLI arguments
- Resolve configuration
- Orchestrate the full pipeline
- Handle exit codes
- Export JSON and/or Markdown output

**Deferred by design:**
- REST API behavior

### JSON Exporter (`src/exporters/json_exporter.py`)

Serializes a `ScoutSchema` into a stable JSON document.

**Public interface:**
- `export(schema: ScoutSchema) -> str`
- `export_to_file(schema, path) -> None`

**Responsibilities:**
- Faithful serialization of canonical schema
- UTF-8 pretty-printed output
- Stable key ordering
- Schema compliance
- Never mutates input schema

**Deferred by design:**
- CLI behavior
- REST API behavior

### Markdown Exporter (`src/exporters/markdown_exporter.py`)

Renders a `ScoutSummary` into a deterministic Markdown document.

**Public interface:**
- `export(summary: Summary) -> str`
- `export_to_file(summary, path) -> None`

**Responsibilities:**
- Exact rendering of summary text
- UTF-8 output
- Never mutates input summary
- Never summarizes, infers, or classifies

**Deferred by design:**
- CLI behavior

### REST API (`src/api/app.py`)

HTTP interface for Scout OSS using FastAPI. Reuses the existing
`RequestHandler.handle()` for pipeline orchestration.

**Public interface:**
- `GET /` - API documentation links
- `GET /health` - Health check
- `GET /version` - Version information
- `POST /scan` - Scan a website

**Responsibilities:**
- HTTP request/response handling
- Request validation
- Error mapping to HTTP status codes
- Automatic OpenAPI/Swagger documentation
- Reuses RequestHandler without duplicating pipeline logic

**Deferred by design:**
- Authentication
- Persistence
- Rate limiting
