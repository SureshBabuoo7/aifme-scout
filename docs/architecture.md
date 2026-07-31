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
- Technology detection
- Content extraction
- Social discovery
- Competitor discovery
- Evidence collection
- Summary Builder
- Exporters

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
- Metadata Extractor
- Technology Detector
- Content Extractor
- Social Discovery
- Competitor Discovery
- Evidence Collector
- Summary Builder
- Exporters
- CLI behavior
- REST API behavior
