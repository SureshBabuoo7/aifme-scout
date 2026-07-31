# AIFME Scout OSS

AIFME Scout OSS is the free, open-source, self-hosted entry point into AIFME's marketing-intelligence capability. Point it at a URL; it returns a structured, evidence-linked snapshot of what a business is, how its site is built, what it says about itself, and how it compares to named competitors — as a CLI, a REST API, and a versioned JSON schema built for both humans and AI agents to consume.

## Current Status

Implementation in progress.

## Development Setup

```bash
git clone https://github.com/aifme/aifme-scout.git
cd aifme-scout
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
pytest
```

## Repository Structure

```
aifme-scout/
├── .github/          # GitHub configuration (CI, issue templates, CODEOWNERS)
├── docs/             # Documentation
├── examples/         # Sample scans and screenshots
├── schemas/          # Versioned JSON schemas
├── tests/            # Test suite
├── src/              # Source code
│   ├── cli/          # CLI module
│   ├── api/          # REST API module
│   ├── engine/       # Orchestration and assembly
│   ├── scanner/      # Fetch and parse
│   ├── extractors/   # Extractor modules
│   ├── exporters/    # Output rendering
│   └── utils/        # Cross-cutting helpers
├── scripts/          # Dev/release tooling
└── assets/           # Static brand/media
```

## Links

- [Documentation](./docs/)
- [Contributing](./CONTRIBUTING.md)
- [Security Policy](./SECURITY.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)
- [Support](./SUPPORT.md)
- [FAQ](./FAQ.md)
