# Changelog

All notable changes to AIFME Scout OSS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-08-05 (Stable Release)

### Added

- Embedded JSON schema in wheel for installed-package compatibility
- Maintenance mode notice and `MAINTENANCE.md` with P0/P1 + security-only policy
- `docs/LIMITATIONS.md` — comprehensive honest limitations reference
- Enhanced FAQ with business-use, licensing, and schema versioning questions
- Contributing guide with DCO and branch naming conventions
- Security policy with 5-business-day response SLA
- Code of Conduct adapted from Contributor Covenant 2.1
- `CITATION.cff` for academic citation
- `NOTICE` file for third-party attributions
- Dependabot configuration for automated dependency updates
- GitHub labels documentation (`labels.yml`)
- Issue templates for bugs, features, and questions
- Pull request template with checklist
- CODEOWNERS for automated review assignment
- GitHub Actions CI with lint, typecheck, test, schema validation, and multi-OS build
- Pre-commit hooks with ruff, black, and mypy
- Comprehensive test suite with 520 passing tests
- Versioned JSON Schema (`schemas/v1/scan-result.schema.json`)
- Deterministic evidence IDs and ordering
- Confidence engine with `confidence`, `scan_status`, `scan_coverage`, and `target_classification`
- 11 deterministic business classifications
- Anti-bot challenge detection (Cloudflare, Imperva, Datadome, CAPTCHA)
- Sitemap discovery and fetching
- Retry logic with exponential backoff for 5xx errors
- Brotli decompression fallback
- Extended SEO extraction (Open Graph, Twitter Cards, hreflang, AMP, JSON-LD)
- Extended content extraction (contact emails/phones, videos, audio, blockquotes, code blocks, definition lists, addresses, figures)
- Extended technology detection (CDN headers, security headers, 20+ JS library fingerprints, HTML comment CMS fingerprints, JS global fingerprints)
- Extended social discovery (10 new platforms, JSON-LD sameAs, Font Awesome icon classes)
- Extended competitor discovery ("vs" headings, schema.org markup)
- REST API with `/health`, `/version`, and `/scan` endpoints
- CLI with configuration precedence, exit codes, and output control
- Markdown exporter with CEO-grade executive intelligence reports
- JSON exporter with stable, pretty-printed, schema-compliant output

### Changed

- Promoted version from `1.0.0-rc2` to `1.0.0` for stable release
- Updated classifier from `Pre-Alpha` to `Production/Stable`
- Redesigned Markdown report for business users with health score, executive summary, and missing data explanations
- Updated report wording to replace technical jargon with plain English equivalents
- Enhanced website classification with more specific business categories and word-boundary matching
- Improved README with badges, screenshots, and improved structure
- Fixed GitHub repository URLs across README, SUPPORT.md, and pyproject.toml
- Fixed README badge rendering (Markdown image syntax converted to HTML for GitHub compatibility)
- Fixed nested HTML tags and duplicate horizontal rules in README
- Fixed CODEOWNERS to reference actual GitHub user
- Removed filesystem-based schema loading fallback; schema now loads exclusively via `importlib.resources`
- Evidence collection increased from ~20 to ~458 avg per site
- Technology detection improved from 0% to 91% site coverage
- Social detection improved from 0% to 64% site coverage
- Scanner retry logic improved with exponential backoff
- Content-Encoding tracking added to scanner

### Fixed

- Critical packaging bug: embedded JSON schema in wheel for installed-package compatibility
- Removed filesystem-based schema loading fallback
- Fixed README badge rendering for GitHub compatibility
- Fixed GitHub repository URLs in README, SUPPORT.md, and pyproject.toml
- Fixed nested HTML tags and duplicate horizontal rules in README
- Fixed CODEOWNERS to reference actual GitHub user
- Fixed competitor page assignment in discovery logic
- Fixed social discovery relative URL resolution
- Fixed classification engine dead code (added education, media, agency scores)
- Added Accept-Language and Accept headers for improved content negotiation

### Validation

- 10-site real-world validation: 9 PASS, 1 LIMITED, 0 FAIL
- 520 tests passing, 0 failing
- No crashes, no regressions
- Deterministic output verified (structural content identical; only timestamps and dynamic headers vary)
- JSON schema compliance verified
- Markdown output verified for all PASS sites
- Fresh wheel installation verified
- CLI verified end-to-end
- Multi-OS build verified (Ubuntu, macOS, Windows)

### Known Limitations

- LLM-backed summary generation is not implemented; template-based summary is used in all cases
- No authentication, persistence, rate limiting, or background jobs
- `jsonschema` type stubs are not installed, causing one mypy import-untyped warning in `extractors/schema.py`
- No plugin system (community extensions should use the `extensions` namespace in JSON output)
- Anti-bot protected sites may return challenge pages instead of actual HTML
- Competitor heuristic discovery requires an explicit `target_classification` parameter
- Technology detection is rule-based and may not detect custom or internal frameworks
- See [docs/LIMITATIONS.md](docs/LIMITATIONS.md) for the complete limitations reference

### Credits

- **Engineering Lead:** Suresh Babu
- **Contributors:** All community contributors who submitted issues, feedback, and pull requests
- **Inspired by:** The AIFME Platform marketing intelligence methodology

---

## [1.0.0-rc2] — 2026-08-04

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

---

## [1.0.0-rc1] — 2026-08-03

### Added

- Website Scanner module with HTTP fetch, robots.txt awareness, SSRF protection, and configurable timeouts
- HTML Parser module with deterministic DOM tree construction and lenient malformed HTML recovery
- SEO Extractor with on-page signal extraction
- Metadata Extractor with structured head metadata extraction
- Technology Detector with rule-based detection
- Content Extractor with structured body content extraction
- Social Discovery with platform detection from page links
- Competitor Discovery with explicit competitor reference detection
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
- `jsonschema` type stubs are not installed, causing one mypy import-untyped warning
- No plugin system (community extensions should use the `extensions` namespace)
- No diagrams in architecture documentation (text descriptions only)

[1.0.0]: https://github.com/SureshBabuoo7/aifme-scout/compare/v1.0.0-rc2...v1.0.0
[1.0.0-rc2]: https://github.com/SureshBabuoo7/aifme-scout/compare/v1.0.0-rc1...v1.0.0-rc2
[1.0.0-rc1]: https://github.com/SureshBabuoo7/aifme-scout/releases/tag/v1.0.0-rc1
