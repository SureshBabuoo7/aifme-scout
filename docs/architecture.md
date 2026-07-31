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

**Deferred by design:**
- HTML parsing
- DOM creation
- Metadata extraction
- Technology detection
- Content extraction
- Social discovery
- Competitor discovery
- Evidence collection
- Summary Builder
- Exporters
