# Release Notes: AIFME Scout OSS v1.0.0-rc2

**Release Candidate 2 — August 3, 2026**

AIFME Scout OSS is the free, open-source, self-hosted entry point into AIFME's marketing-intelligence capability. This release makes Scout OSS publicly available for the first time.

## Highlights

- **Improved Technology Detection**: Added detection rules for GitHub, Primer CSS, Turbo/Hotwire, jQuery, Adobe Helix, Zoho, Astro, Cloudflare, and OneTrust
- **Competitor Discovery Fixes**: Added developer-tools heuristic category and fixed competitor page assignment
- **Social Discovery Improvements**: Fixed relative URL resolution
- **Scanner Reliability**: Added Brotli decompression fallback for sites like vercel.com
- **Professional Repository**: Redesigned README, added badges, screenshots, issue templates, and PR template
- **Version Bump**: Runtime version updated to `1.0.0-rc2`

## Installation

```bash
pip install aifme-scout
```

## Quick Start

```bash
# Scan a website
aifme-scout scan https://www.python.org

# Or run as a module
python -m aifme_scout scan https://www.python.org
```

## Breaking Changes

None. This is a release candidate. API and schema may change before final `1.0.0`.

## Known Limitations

- LLM-backed summary generation is not implemented; template-based summary is used in all cases
- No authentication, persistence, rate limiting, or background jobs
- This is a release candidate; API and schema may change before final `1.0.0`
- `jsonschema` type stubs are not installed, causing one mypy import-untyped warning
- No plugin system (community extensions should use the `extensions` namespace)
- Anti-bot protected sites (e.g., openai.com, docker.com) may return challenge pages instead of actual HTML, resulting in minimal extracted evidence. This is expected behavior.
- Competitor heuristic discovery requires an explicit `target_classification` parameter
- Technology detection is rule-based and may not detect custom or internal frameworks

## Full Changelog

See [CHANGELOG.md](./CHANGELOG.md) for the complete history.

## Documentation

- [README](./README.md)
- [Contributing](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [FAQ](./FAQ.md)
- [Roadmap](./ROADMAP.md)
