# AIFME Scout OSS

AIFME Scout OSS is the free, open-source, self-hosted entry point into AIFME's marketing-intelligence capability. Point it at a URL; it returns a structured, evidence-linked snapshot of what a business is, how its site is built, what it says about itself, and how it compares to named competitors — as a CLI, a REST API, and a versioned JSON schema built for both humans and AI agents to consume.

## Features

- **Website Scanning** — Safely fetch and analyze websites with configurable timeouts, crawl delays, and SSRF protection.
- **HTML Parsing** — Convert raw HTML into a deterministic, navigable DOM tree with lenient recovery for malformed markup.
- **SEO Extraction** — Extract on-page SEO signals including titles, meta descriptions, canonical URLs, heading hierarchy, Open Graph, Twitter Cards, and structured data.
- **Metadata Extraction** — Pull structured head metadata including favicons, language, manifest links, RSS/Atom feeds, and verification tags.
- **Technology Detection** — Identify frameworks, CMS platforms, web servers, analytics tools, and CSS frameworks with rule-based confidence.
- **Content Extraction** — Extract structured body content including headings, paragraphs, lists, tables, images, links, buttons, forms, breadcrumbs, and footers.
- **Social Discovery** — Find linked social profiles from parsed page links with platform detection and provenance tracking.
- **Competitor Discovery** — Assemble competitor comparison sets from explicit declarations and user-supplied lists.
- **Evidence Collection** — Normalize all extractor outputs into a common, traceable evidence model with deterministic IDs.
- **Schema Validation** — Validate every scan result against a versioned JSON Schema before export.
- **JSON Export** — Pretty-printed, schema-compliant JSON output with stable key ordering.
- **Markdown Export** — Deterministic Markdown reports preserving all section headings and evidence references.
- **CLI** — Full-featured command-line interface with configuration precedence, exit codes, and output control.
- **REST API** — FastAPI-based HTTP interface with automatic OpenAPI/Swagger documentation.

## Why Scout OSS Exists

Scout OSS performs the **Understand** step of the AIFME model and nothing past it. It has no persistent memory, no reasoning or decision logic, and no ability to act on a target's behalf. It is a standalone extraction toolkit that gives you a structured, evidence-linked snapshot of a website's public-facing identity — ready for humans or AI agents to consume.

The commercial AIFME Platform includes Remember, Reason, Decide, Execute, and Measure capabilities. Scout OSS is the open-source foundation: the free, self-hosted way to gather and understand web intelligence.

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or compatible package manager

### Install from PyPI

```bash
pip install aifme-scout
```

### Editable Install (Development)

```bash
git clone https://github.com/aifme/aifme-scout.git
cd aifme-scout
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Quick Start

### CLI

Scan a website and generate both JSON and Markdown output:

```bash
aifme-scout scan https://example.com
```

Output files are written to the current directory:
- `scan-result.json` — Schema-validated JSON report
- `report.md` — Markdown summary

### REST API

Start the API server:

```bash
uvicorn aifme_scout.api.app:app --host 0.0.0.0 --port 8000
```

Scan a website:

```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

Interactive documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## CLI Examples

### Basic scan

```bash
aifme-scout scan https://example.com
```

### JSON output only

```bash
aifme-scout scan https://example.com --output json --out ./reports
```

### Markdown output only

```bash
aifme-scout scan https://example.com --output markdown --out ./reports
```

### Custom timeout and user agent

```bash
aifme-scout scan https://example.com --timeout 30 --user-agent "MyBot/1.0"
```

### Verbose mode

```bash
aifme-scout scan https://example.com --verbose
```

### Quiet mode

```bash
aifme-scout scan https://example.com --quiet
```

## REST API Examples

### Health check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "version": "1.0.0-rc1"
}
```

### Version

```bash
curl http://localhost:8000/version
```

### Scan with custom options

```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "output": "both",
    "timeout": 15.0,
    "user_agent": "MyBot/1.0",
    "mode": "no-llm"
  }'
```

## Output Formats

### JSON

The JSON Exporter produces a stable, pretty-printed document that validates against `schemas/v1/scan-result.schema.json`.

```json
{
  "meta": {
    "schema_version": "1.0.0",
    "engine_version": "0.12.0",
    "timestamp": "2024-01-01T00:00:00+00:00"
  },
  "site": {
    "url": "https://example.com",
    "target_url": "https://example.com"
  },
  "seo": [],
  "metadata": [],
  "technology": [],
  "content": [],
  "social": [],
  "competitors": [],
  "evidence": [],
  "diagnostics": {
    "total_evidence_items": 0,
    "seo_items": 0,
    "metadata_items": 0,
    "technology_items": 0,
    "content_items": 0,
    "social_items": 0,
    "competitor_items": 0,
    "build_timestamp": "2024-01-01T00:00:00+00:00"
  }
}
```

### Markdown

The Markdown Exporter renders the `ScoutSummary` exactly as produced by the Summary Builder:

```markdown
## Executive Summary

Target site: https://example.com
Evidence items collected: 0

## Website Overview

URL: https://example.com
Schema version: 1.0.0

## Diagnostics

total_evidence_items: 0
seo_items: 0
...
```

## Architecture Overview

Scout OSS follows a deterministic, stateless pipeline:

1. **Website Scanner** — Fetches raw HTML with transport metadata
2. **HTML Parser** — Builds a navigable DOM tree
3. **SEO Extractor** — Derives on-page SEO signals
4. **Metadata Extractor** — Extracts structured head metadata
5. **Technology Detector** — Identifies technology fingerprints
6. **Content Extractor** — Extracts structured body content
7. **Social Discovery** — Finds linked social profiles
8. **Competitor Discovery** — Assembles competitor comparison sets
9. **Evidence Collector** — Normalizes extractor outputs into evidence items
10. **Schema Builder** — Assembles and validates the `ScoutSchema`
11. **Summary Builder** — Generates deterministic, evidence-linked summaries
12. **JSON Exporter** — Serializes schema to stable JSON
13. **Markdown Exporter** — Renders summary to Markdown

The **Request Handler** is the single orchestration entry point for both the CLI and REST API.

## Repository Structure

```
aifme-scout/
├── .github/              # GitHub configuration (CI, issue templates, CODEOWNERS)
├── docs/                 # Documentation
│   ├── architecture.md   # Module-level architecture documentation
│   ├── api-guide.md      # API usage and examples
│   ├── cli-guide.md      # CLI usage and examples
│   ├── schema.md         # JSON Schema documentation
│   ├── faq.md            # Frequently asked questions
│   └── migration-guide.md # Migration guidance
├── examples/             # Sample scans and screenshots
├── schemas/              # Versioned JSON schemas
│   └── v1/
│       └── scan-result.schema.json
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── src/                  # Source code
│   ├── aifme_scout/
│   │   ├── cli/          # CLI module
│   │   ├── api/          # REST API module (FastAPI)
│   │   ├── engine/       # Orchestration and assembly
│   │   ├── scanner/      # Fetch and transport
│   │   ├── parser/       # HTML parsing
│   │   ├── extractors/   # Extraction modules
│   │   ├── exporters/    # Output rendering
│   │   └── utils/        # Cross-cutting helpers
├── scripts/              # Dev/release tooling
└── assets/               # Static brand/media
```

## Development Setup

```bash
git clone https://github.com/aifme/aifme-scout.git
cd aifme-scout
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aifme_scout --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_cli.py
```

## Code Quality

```bash
# Lint
ruff check src/ tests/

# Type check
mypy src/

# Format check
black --check src/ tests/
```

## License

This project is licensed under the [Apache License 2.0](./LICENSE).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup, testing, and pull request guidelines.

## Links

- [Documentation](./docs/)
- [Contributing](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Support](./SUPPORT.md)
- [FAQ](./FAQ.md)
- [Changelog](./CHANGELOG.md)
