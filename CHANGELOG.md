## Unreleased

### Changed

- Finalized CEO-grade executive intelligence report with business-friendly language, deterministic health scoring, and section-level takeaways
- Added reusable Markdown renderer module for consistent report styling
- Updated report wording to replace technical jargon with plain English equivalents
- Enhanced website classification with more specific business categories
- Updated README to reflect current report capabilities

## 1.0.0-rc1

### Added

- Website Scanner module with HTTP fetch, robots.txt awareness, SSRF protection, and configurable timeouts
- HTML Parser module with deterministic DOM tree construction and lenient malformed HTML recovery
- SEO Extractor with on-page signal extraction (titles, meta descriptions, canonical URLs, heading hierarchy, Open Graph, Twitter Cards, structured data)
- Metadata Extractor with structured head metadata extraction (favicons, language, manifests, RSS/Atom feeds, verification tags)
- Technology Detector with rule-based framework, CMS, web server, analytics, and CSS framework detection
- Content Extractor with structured body content extraction (headings, paragraphs, lists, tables, images, links, buttons, forms, breadcrumbs, footers)
- Social Discovery with platform detection from page links and provenance tracking
- Competitor Discovery with explicit competitor reference detection and user-supplied competitor inclusion
- Evidence Collector with normalization, deterministic ID generation, and duplicate elimination
- Schema Builder with `ScoutSchema` assembly and JSON Schema validation
- Summary Builder with deterministic, evidence-linked Markdown summaries
- JSON Exporter with stable, pretty-printed, schema-compliant output
- Markdown Exporter with exact summary text rendering
- Command Line Interface (`aifme-scout scan`) with configuration precedence, exit codes, and output control
- REST API (FastAPI) with `/health`, `/version`, and `/scan` endpoints
- OpenAPI/Swagger automatic documentation
- Versioned JSON Schema (`schemas/v1/scan-result.schema.json`)
- Configuration subsystem with CLI flags, environment variables, config file, and built-in defaults
- Structured logging with URL redaction

### Implemented

- Complete Scout OSS pipeline: Scanner → Parser → SEO → Metadata → Technology → Content → Social → Competitors → Evidence → Schema → Summary → JSON/Markdown Export
- Request Handler as single orchestration entry point for both CLI and REST API
- Deterministic, stateless, thread-safe module design
- Frozen dataclass models for immutability
- Comprehensive test suite with 424 passing tests
- Ruff linting, mypy type checking, and pytest test runner integration

### Architecture

- Frozen Architecture v1.0 with 13 implemented modules
- Clear separation of concerns: scanner, parser, extractors, engine, exporters, CLI, API
- Deferred-by-design items: authentication, persistence, rate limiting, LLM-backed summary generation, plugin system

### Documentation

- README with project overview, features, installation, quick start, examples, architecture, and contribution guidelines
- Architecture documentation for all 13 implemented modules
- API Guide with Request Handler, JSON Exporter, Markdown Exporter, and REST API documentation
- CLI Guide with command reference, options, examples, exit codes, and configuration
- Schema documentation with versioning, field descriptions, and validation rules
- Contributing Guide with development setup, testing, linting, and PR guidelines
- FAQ with project scope and platform differentiation

### Testing

- 424 unit and integration tests covering all modules
- CLI tests for help, version, scan command, output formats, and exit codes
- REST API tests for health, version, scan, OpenAPI, and error handling
- Exporter tests for JSON and Markdown serialization, file export, UTF-8, round-trip, and deterministic output
- Schema tests for validation, stability, and versioning

### Known Limitations

- LLM-backed summary generation falls back to template mode when no provider is configured
- No authentication, persistence, rate limiting, or background jobs
- Version `1.0.0-rc1` is a release candidate; API and schema may change before final `1.0.0`
- `jsonschema` type stubs are not installed, causing one mypy import-untyped warning in `extractors/schema.py`
- No plugin system (community extensions should use the `extensions` namespace in JSON output)
- No diagrams in architecture documentation (text descriptions only)

## 1.0.0-rc2

### Added

- Improved technology detection rules for GitHub, Primer CSS, Turbo/Hotwire, jQuery, Adobe Helix, Zoho, Astro, Cloudflare, and OneTrust
- Developer-tools heuristic category for competitor discovery
- Brotli decompression fallback for improved scanner reliability

### Fixed

- Competitor page assignment in discovery logic
- Social discovery relative URL resolution

### Changed

- Redesigned README with badges, screenshots, and improved structure
- Added issue templates and PR template
- Updated project metadata for public launch

### Known Limitations

- LLM-backed summary generation is not implemented; template-based summary is used in all cases
- No authentication, persistence, rate limiting, or background jobs
- This is a release candidate; API and schema may change before final `1.0.0`
- `jsonschema` type stubs are not installed, causing one mypy import-untyped warning
- No plugin system (community extensions should use the `extensions` namespace)
- Anti-bot protected sites may return challenge pages instead of actual HTML
- Competitor heuristic discovery requires an explicit `target_classification` parameter
- Technology detection is rule-based and may not detect custom or internal frameworks

## 1.0.0rc3

### Fixed

- Critical packaging bug: embedded JSON schema in wheel for installed-package compatibility
- Removed filesystem-based schema loading fallback; schema now loads exclusively via `importlib.resources`
- Fixed README badge rendering (Markdown image syntax converted to HTML for GitHub compatibility)
- Fixed GitHub repository URLs in README, SUPPORT.md, and pyproject.toml
- Fixed nested HTML tags and duplicate horizontal rules in README
- Fixed CODEOWNERS to reference actual GitHub user

### Changed

- Bumped version from `1.0.0-rc2` to `1.0.0rc3` for PEP 440 compliance
- Updated classifier from Pre-Alpha to Beta
- Redesigned Markdown report for business users with health score, executive summary, and missing data explanations
- Added maintenance mode notice to README
- Added MAINTENANCE.md with P0/P1 + security-only policy

### Known Limitations

- LLM-backed summary generation is not implemented; template-based summary is used in all cases
- No authentication, persistence, rate limiting, or background jobs
- This is a release candidate; API and schema may change before final `1.0.0`
- `jsonschema` type stubs are not installed, causing one mypy import-untyped warning
- No plugin system (community extensions should use the `extensions` namespace)
- Anti-bot protected sites may return challenge pages instead of actual HTML
- Competitor heuristic discovery requires an explicit `target_classification` parameter
- Technology detection is rule-based and may not detect custom or internal frameworks
