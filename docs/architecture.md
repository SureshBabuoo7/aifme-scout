# Architecture

AIFME Scout OSS follows a deterministic, stateless pipeline. The same orchestration logic is shared by the CLI and REST API through a single Request Handler.

## Design Principles

- **Deterministic** — Identical input produces identical output
- **Stateless** — No in-memory state between scans
- **Immutable** — All data models are frozen dataclasses
- **Thread-safe** — No mutable shared state
- **Provenance-tracked** — Every evidence item traces to its source

## Pipeline

```
┌─────────────────┐
│  Website Scanner │──────┐
└─────────────────┘      │
                         ▼
┌─────────────────┐  ┌───────────┐
│   HTML Parser   │──▶│   RawSite │
└─────────────────┘  └─────┬─────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │   SEO    │   │ Metadata │   │Technology │
    │Extractor │   │Extractor │   │ Detector  │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │               │               │
         ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │ Content  │   │  Social  │   │Competitor│
    │Extractor │   │Discovery │   │Discovery │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
                  ┌─────────────┐
                  │   Evidence  │
                  │  Collector  │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   Schema    │
                  │   Builder   │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   Summary   │
                  │   Builder   │
                  └──────┬──────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
      ┌──────────┐            ┌──────────┐
      │   JSON   │            │ Markdown │
      │ Exporter │            │ Exporter │
      └──────────┘            └──────────┘
```

## Modules

### Request Handler (`engine/`)

The single orchestration entry point for both CLI and REST API.

- `handle(request) -> ScanResult` — Validates, orchestrates, and assembles the final result
- No pipeline logic is duplicated across interfaces

### Website Scanner (`scanner/`)

Fetches website resources safely and deterministically.

- HTTP GET with configurable timeout
- Safe redirect following
- robots.txt awareness
- SSRF protection
- Retry logic with exponential backoff
- Anti-bot challenge detection

### HTML Parser (`parser/`)

Converts raw HTML into a deterministic, navigable DOM tree.

- Lenient malformed HTML recovery
- Head/body region isolation
- Character encoding handling

### Extractor Modules (`extractors/`)

| Module | Purpose |
|--------|---------|
| SEO | On-page SEO signals (titles, meta, canonical, Open Graph, Twitter Cards, hreflang, AMP) |
| Metadata | Structured head metadata (favicons, language, manifests, feeds, verification tags) |
| Technology | Framework, CMS, server, analytics, CSS, CDN, and security header detection |
| Content | Structured body content (headings, paragraphs, lists, tables, images, links, forms) |
| Social | Platform detection from page links, JSON-LD sameAs, icon classes |
| Competitors | Explicit declarations, "vs" headings, schema.org markup, user-supplied lists |
| Evidence | Normalization, deterministic IDs, duplicate elimination, provenance preservation |
| Schema | ScoutSchema assembly and JSON Schema validation |

### Engine (`engine/`)

- `summary.py` — Deterministic, evidence-linked summary generation
- `request_handler.py` — Pipeline orchestration and configuration resolution

### Exporters (`exporters/`)

| Exporter | Purpose |
|----------|---------|
| JSON | Schema-validated, pretty-printed, stable key ordering |
| Markdown | CEO-grade executive intelligence reports |

### CLI (`cli/`)

Full-featured command-line interface:

- Configuration precedence: CLI flags > env vars > config file > defaults
- Exit codes for error categorization
- Output control (json, markdown, both)

### REST API (`api/`)

FastAPI-based HTTP interface:

- `GET /` — API documentation links
- `GET /health` — Health check
- `GET /version` — Version information
- `POST /scan` — Scan a website
- Automatic OpenAPI/Swagger at `/docs` and `/redoc`

## Data Flow

1. **Input**: `ScanRequest(target_url, competitor_urls, mode, options)`
2. **Scan**: `ScannerService.scan()` → `RawSite`
3. **Parse**: `parse(RawSite)` → `ParsedSite`
4. **Extract**: Eight extractor modules → `SEO`, `Metadata`, `Technology`, `Content`, `Social`, `Competitors`, `Evidence`, `Schema`
5. **Collect**: `collect()` → `EvidenceCollection` with deterministic IDs
6. **Build**: `ScoutSchema` assembly and JSON Schema validation
7. **Summarize**: `summarize()` → `Summary` with evidence-linked text
8. **Export**: JSON string + Markdown string

## Thread Safety

All modules are immutable and thread-safe. No module maintains mutable state between invocations.

## Determinism

- Evidence IDs are deterministic for identical input
- Sorting is applied where ordering matters
- Timestamps are ISO-8601 UTC
- Dynamic HTTP headers (e.g., `cf-ray`) are expected to vary between runs

## See Also

- [Schema](schema.md) — JSON Schema documentation
- [API Guide](api-guide.md) — Request Handler and REST API reference
- [CLI Guide](cli-guide.md) — Command-line usage
- [Plugin Guide](plugin-guide.md) — Extension and plugin development
