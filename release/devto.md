# dev.to Post

# Introducing AIFME Scout OSS v1.0.0 — Open-Source Website Intelligence

We're excited to announce the stable release of **AIFME Scout OSS v1.0.0**, a free and open-source Python toolkit for structured website intelligence.

## What is AIFME Scout OSS?

AIFME Scout OSS scans any public URL and produces a deterministic, evidence-linked snapshot of a website's:

- Technology stack (frameworks, CMS, servers, analytics, security headers)
- SEO signals (titles, meta descriptions, Open Graph, Twitter Cards, structured data)
- Structured content (headings, paragraphs, lists, tables, images, links)
- Metadata (favicons, language, feeds, verification tags)
- Social profiles (platform detection from page links)
- Competitor references (explicit mentions, schema.org markup)

The output is a versioned JSON schema and a Markdown executive report.

## Quick Start

```bash
pip install aifme-scout
aifme-scout scan https://www.python.org
```

That's it. You get `scan-result.json` and `report.md` in your current directory.

## Architecture

Scout OSS follows a deterministic, stateless pipeline:

```
Scanner → Parser → Extractors → Evidence → Schema → Summary → JSON + Markdown
```

All modules are frozen, immutable, and thread-safe. The same orchestration logic is shared by the CLI and REST API.

## Validation

We ran the toolkit against 10 real-world websites:

| Site | Status | Evidence |
|------|--------|----------|
| python.org | PASS | 347 |
| github.com | PASS | 446 |
| cloudflare.com | PASS | 6174 |
| wordpress.org | PASS | 1386 |
| openai.com | PASS | 154 |
| mozilla.org | PASS | 459 |
| apple.com | PASS | 778 |
| microsoft.com | PASS | 262 |
| example.com | PASS | 12 |
| reddit.com | LIMITED | — |

9 PASS, 1 LIMITED (reddit.com robots.txt), 0 FAIL. 520 tests passing, 0 crashes.

## Key Features

- **CLI + REST API** — Full-featured command-line interface and FastAPI HTTP interface
- **Evidence-linked reports** — Every claim traces to a deterministic evidence item with provenance
- **11 business classifications** — Deterministic categorization with confidence scores
- **Safe scanning** — SSRF protection, robots.txt awareness, retry logic, anti-bot detection
- **Deterministic output** — Identical input produces identical output
- **Apache 2.0** — Permissive license for commercial and personal use

## Limitations

AIFME Scout OSS is intentionally scoped:

- No JavaScript execution (static HTML only)
- Anti-bot protection is respected, not bypassed
- No persistent memory or reasoning logic
- Technology detection is rule-based

See the full [Limitations](https://github.com/SureshBabuoo7/aifme-scout/blob/master/docs/LIMITATIONS.md) documentation.

## Maintenance Mode

Scout OSS is in **maintenance mode** as of v1.0.0. Only P0/P1 bug fixes and security updates are accepted. Community contributions are still welcome.

## Links

- GitHub: https://github.com/SureshBabuoo7/aifme-scout
- PyPI: https://pypi.org/project/aifme-scout/
- Documentation: https://github.com/SureshBabuoo7/aifme-scout/blob/master/docs

We built Scout OSS to be the kind of tool we wish existed when we were doing competitive intelligence and SEO audits. We hope you find it useful.
