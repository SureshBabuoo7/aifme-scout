# Release Notes: AIFME Scout OSS v1.0.0rc3

**Release Candidate 3 — August 4, 2026**

AIFME Scout OSS is the free, open-source, self-hosted entry point into AIFME's marketing-intelligence capability.

## Highlights

- **Packaging Fix**: Embedded JSON schema in wheel for installed-package compatibility
- **Schema Loading**: Removed filesystem-based fallback; schema now loads exclusively via `importlib.resources`
- **README Fixes**: Fixed badge rendering, repository URLs, nested HTML tags, and duplicate horizontal rules
- **Report Redesign**: Completely redesigned Markdown report for business users with health score, executive summary, and missing data explanations
- **Maintenance Mode**: Added maintenance mode notice and MAINTENANCE.md with P0/P1 + security-only policy
- **Version Bump**: Updated to `1.0.0rc3` for PEP 440 compliance

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
- Anti-bot protected sites may return challenge pages instead of actual HTML
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
- [Support](./SUPPORT.md)
- [Maintenance](./MAINTENANCE.md)
