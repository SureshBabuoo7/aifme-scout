# Release Notes: AIFME Scout OSS 1.0.0-rc2

## Overview

AIFME Scout OSS is the free, open-source, self-hosted entry point into AIFME's marketing-intelligence capability. This release candidate makes Scout OSS publicly available for the first time.

Scout OSS scans a URL and returns a structured, evidence-linked snapshot of what a business is, how its site is built, what it says about itself, and how it compares to named competitors. Output is provided as a CLI tool, a REST API, and a versioned JSON schema.

## What's New in RC-02

### Technology Detection Improvements

- **GitHub detection**: Identifies `server: github.com` HTTP header
- **Primer CSS detection**: Detects GitHub's Primer CSS framework via `primer-` link URLs
- **Turbo/Hotwire detection**: Identifies Turbo/Hotwire via `turbo-` meta tags and script URLs
- **jQuery detection**: Detects jQuery via script URL fingerprints
- **Adobe Helix detection**: Identifies Adobe Helix CMS via script URLs
- **Zoho detection**: Detects Zoho SaaS platform via `server: ZGS` header and script URLs
- **Astro detection**: Identifies Astro framework via `/_astro/` script URLs
- **Cloudflare detection**: Identifies Cloudflare infrastructure via `server: cloudflare` header
- **Cloudflare Insights detection**: Detects Cloudflare analytics via script URLs
- **OneTrust detection**: Identifies OneTrust compliance via `otSDKStub` script URLs
- **Case-insensitive header lookup**: Fixed HTTP header matching to handle lowercase header names

### Competitor Discovery Improvements

- **Developer-tools category**: Added heuristic competitor discovery for developer-tools classification (GitLab, Bitbucket, Gitea, SourceForge, GitKraken)
- **Heuristic competitor assignment**: Fixed a bug where heuristic competitors were generated but never assigned to any page. Heuristic competitors are now included on the first page of the scan result.

### Social Discovery Improvements

- **Relative URL resolution**: Relative URLs (e.g., `about.html`) are now resolved to absolute URLs instead of being silently dropped

### Scanner Improvements

- **Brotli decompression fallback**: Added automatic fallback to gzip/deflate when Brotli decompression fails (e.g., on vercel.com)

### Bug Fixes

- Fixed HTTP header case-insensitivity in technology detection
- Fixed protocol-relative URL resolution in competitor discovery
- Fixed social discovery URL normalization for relative links
- Fixed heuristic competitor page assignment

### Documentation

- Updated README.md with professional hero section, badges, architecture diagram, and integrated FAQ
- Added release notes for RC-02

## System Requirements

- Python 3.11 or higher
- pip or compatible package manager

## Installation

```bash
pip install aifme-scout
```

## CLI

```bash
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

Schema version is `1.0.0`. Engine version is `1.0.0-rc2`.

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
- Anti-bot protected sites (e.g., openai.com, docker.com) may return challenge pages instead of actual HTML, resulting in minimal extracted evidence. This is expected behavior — the scanner faithfully returns whatever HTML the target serves.
- Competitor heuristic discovery requires an explicit `target_classification` parameter. Without it, only explicit competitor declarations (from comparison/alternative pages) and user-supplied competitors are discovered.
- Technology detection is rule-based and may not detect custom or internal frameworks.

## Upgrade Notes

This is the second public release candidate. There are no prior versions to upgrade from.

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
- [Roadmap](./ROADMAP.md)
