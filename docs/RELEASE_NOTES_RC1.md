# Release Notes: AIFME Scout OSS 1.0.0-rc1

## Overview

AIFME Scout OSS is the free, open-source, self-hosted entry point into AIFME's marketing-intelligence capability. This release candidate makes Scout OSS publicly available for the first time.

Scout OSS scans a URL and returns a structured, evidence-linked snapshot of what a business is, how its site is built, what it says about itself, and how it compares to named competitors. Output is provided as a CLI tool, a REST API, and a versioned JSON schema.

## Major Capabilities

- **Website Scanning** — Safe, deterministic HTTP fetching with SSRF protection, robots.txt awareness, configurable timeouts, and crawl delays
- **HTML Parsing** — Lenient DOM tree construction from raw HTML with encoding handling and malformed markup recovery
- **SEO Extraction** — On-page SEO signals: titles, meta descriptions, canonical URLs, heading hierarchy, Open Graph, Twitter Cards, structured data, and indexability flags
- **Metadata Extraction** — Structured head metadata: favicons, language, manifests, RSS/Atom feeds, verification tags, and web app capable flags
- **Technology Detection** — Framework, CMS, web server, analytics, and CSS framework detection with rule-based confidence
- **Content Extraction** — Structured body content: headings, paragraphs, lists, tables, images, links, buttons, forms, breadcrumbs, and footers
- **Social Discovery** — Linked social profile detection with platform identification and provenance tracking
- **Competitor Discovery** — Explicit competitor reference discovery and user-supplied competitor inclusion
- **Evidence Collection** — Normalized, traceable evidence model with deterministic IDs and duplicate elimination
- **Schema Validation** — Every scan result validates against `schemas/v1/scan-result.schema.json` before export
- **JSON Export** — Pretty-printed, UTF-8 encoded, schema-compliant JSON with stable alphabetical key ordering
- **Markdown Export** — Deterministic Markdown reports preserving all section headings, wording, and evidence references
- **CLI** — Full-featured command-line interface with `aifme-scout scan <url>`, configuration precedence, and exit codes
- **REST API** — FastAPI-based HTTP interface with automatic OpenAPI/Swagger documentation

## Architecture Summary

Scout OSS follows a deterministic, stateless pipeline:

```
Website Scanner → HTML Parser → SEO Extractor → Metadata Extractor →
Technology Detector → Content Extractor → Social Discovery →
Competitor Discovery → Evidence Collector → Schema Builder →
Summary Builder → JSON Exporter / Markdown Exporter
```

The **Request Handler** is the single orchestration entry point for both the CLI and REST API. No pipeline logic is duplicated across interfaces.

All modules are frozen, immutable, and thread-safe. The JSON Schema is versioned independently from the engine version.

## CLI

```bash
# Install
pip install aifme-scout

# Scan a website
aifme-scout scan https://example.com

# Options
aifme-scout scan https://example.com --output json --out ./reports
aifme-scout scan https://example.com --output markdown --out ./reports
aifme-scout scan https://example.com --timeout 30 --user-agent "MyBot/1.0"
aifme-scout scan https://example.com --verbose
aifme-scout scan https://example.com --quiet
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments or configuration error |
| 2 | Network failure |
| 3 | Scanner failure |
| 4 | Parser failure |
| 5 | Internal error |

## REST API

```bash
# Start server
uvicorn aifme_scout.api.app:app --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/health

# Scan
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "mode": "no-llm"}'
```

Interactive documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## JSON Schema

The canonical schema is `schemas/v1/scan-result.schema.json`. It defines:

- `meta` — schema version, engine version, timestamp
- `site` — target URL identifiers
- `seo`, `metadata`, `technology`, `content`, `social`, `competitors` — sectioned evidence arrays
- `evidence` — flat, authoritative evidence list
- `diagnostics` — build-time counters and timestamps

Schema version is `1.0.0`. Engine version is `1.0.0-rc1`.

## Markdown Reports

The Markdown Exporter renders the `ScoutSummary` exactly as produced by the Summary Builder. Sections include:

1. Executive Summary
2. Website Overview
3. SEO Summary
4. Metadata Summary
5. Technology Summary
6. Content Summary
7. Social Presence Summary
8. Competitor Summary
9. Diagnostics
10. Data Completeness

All evidence references are preserved. No additional text is injected.

## Known Limitations

- LLM-backed summary generation is not implemented; template-based summary is used in all cases
- No authentication, persistence, rate limiting, or background jobs
- This is a release candidate; API and schema may change before final `1.0.0`
- `jsonschema` type stubs are not installed, causing one mypy import-untyped warning
- No plugin system (community extensions should use the `extensions` namespace)
- No diagrams in architecture documentation

## Upgrade Notes

This is the first public release. There are no prior versions to upgrade from.

- Package name: `aifme-scout`
- Python requirement: `>=3.11`
- Install: `pip install aifme-scout`
- Editable install: `pip install -e ".[dev]"`

## Links

- [Documentation](./docs/)
- [Contributing](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Support](./SUPPORT.md)
- [FAQ](./FAQ.md)
- [Changelog](./CHANGELOG.md)
