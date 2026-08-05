# Hashnode Post

# AIFME Scout OSS v1.0.0 — Open-Source Website Intelligence Toolkit

Today we're releasing **AIFME Scout OSS v1.0.0**, a free and open-source Python toolkit for structured website intelligence.

## The Problem

When we started doing competitive intelligence and SEO audits, we found ourselves cobbling together scripts, APIs, and tools that didn't talk to each other. The output was unstructured, unverified, and hard to compare across sites.

We wanted a tool that:

- Scans a URL safely and deterministically
- Extracts structured data with provenance
- Outputs machine-readable JSON and human-readable Markdown
- Is open source and self-hosted

So we built one.

## What is AIFME Scout OSS?

AIFME Scout OSS scans any public URL and produces a deterministic, evidence-linked snapshot of a website's technology stack, SEO signals, content, metadata, social profiles, and competitor references.

It outputs:
- **scan-result.json** — Schema-validated JSON with 1,386+ evidence items for a typical site
- **report.md** — CEO-grade Markdown report with health score and evidence-linked takeaways

## Quick Example

```bash
pip install aifme-scout
aifme-scout scan https://www.python.org
```

That's it. You get structured output in seconds.

## Validation

We ran Scout OSS against 10 real-world websites:

| Site | Status | Evidence Items |
|------|--------|---------------|
| python.org | PASS | 347 |
| github.com | PASS | 446 |
| cloudflare.com | PASS | 6,174 |
| wordpress.org | PASS | 1,386 |
| openai.com | PASS | 154 |
| mozilla.org | PASS | 459 |
| apple.com | PASS | 778 |
| microsoft.com | PASS | 262 |
| example.com | PASS | 12 |
| reddit.com | LIMITED | — |

**9 PASS, 1 LIMITED (robots.txt), 0 FAIL.** 520 tests passing. Zero crashes.

## Architecture

Scout OSS follows a deterministic, stateless pipeline:

```
Scanner → Parser → 7 Extractors → Evidence Collector → Schema Builder → Summary Builder → JSON + Markdown Exporters
```

All modules are frozen, immutable, and thread-safe. The same orchestration logic is shared by the CLI and REST API.

## Key Features

- **Website Scanning** — Safe HTTP fetch with SSRF protection, robots.txt awareness, configurable timeouts, retry logic
- **HTML Parsing** — Lenient DOM tree construction with deterministic extraction
- **SEO Extraction** — Titles, meta, canonical, Open Graph, Twitter Cards, hreflang, AMP, structured data
- **Technology Detection** — 20+ frameworks, CMS, servers, analytics, CSS, CDN, security headers
- **Content Extraction** — Headings, paragraphs, lists, tables, images, links, forms, contact info
- **Social Discovery** — Platform detection from page links, JSON-LD sameAs, icon classes
- **Competitor Discovery** — Explicit mentions, "vs" headings, schema.org markup
- **Evidence Collection** — Deterministic IDs, provenance tracking, confidence levels
- **Schema Validation** — Every result validated against versioned JSON Schema
- **CLI + REST API** — Full-featured command-line interface and FastAPI HTTP interface

## Honest Limitations

AIFME Scout OSS is intentionally scoped:

- No JavaScript execution (static HTML only)
- Anti-bot protection is respected, not bypassed
- No persistent memory or reasoning logic
- Technology detection is rule-based

See the full [Limitations](https://github.com/SureshBabuoo7/aifme-scout/blob/master/docs/LIMITATIONS.md) documentation.

## Links

- **GitHub:** https://github.com/SureshBabuoo7/aifme-scout
- **PyPI:** https://pypi.org/project/aifme-scout/
- **Documentation:** https://github.com/SureshBabuoo7/aifme-scout/blob/master/docs
- **License:** Apache 2.0

We built Scout OSS to be the kind of tool we wish existed when we were doing competitive intelligence and SEO audits. We hope you find it useful.
