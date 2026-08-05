# AIFME Scout OSS v1.0.0 — General Announcement

We are excited to announce the stable release of **AIFME Scout OSS v1.0.0**, a free, open-source website and marketing intelligence toolkit.

## What is AIFME Scout OSS?

AIFME Scout OSS scans any public URL and produces a deterministic, evidence-linked snapshot of a website's technology stack, SEO signals, structured content, metadata, social profiles, and competitor references. It exposes both a command-line interface and a REST API, and outputs a versioned JSON schema alongside a Markdown executive report.

It is the open-source foundation of the AIFME Platform's **Understand** capability — no persistent memory, no reasoning logic, no action on a target's behalf. Just clean, structured extraction.

## Key Features

- **Website Scanning** — Safe HTTP fetch with SSRF protection, robots.txt awareness, and retry logic
- **11 Business Classifications** — Deterministic categorization from SaaS Platform to Government
- **Technology Detection** — 20+ frameworks, CMS, servers, analytics, and security headers
- **SEO Extraction** — Titles, meta descriptions, Open Graph, Twitter Cards, structured data, hreflang, AMP
- **Evidence-Linked Reports** — Every claim traces to a deterministic evidence item with provenance
- **Dual Output** — Schema-validated JSON and CEO-grade Markdown reports
- **CLI + REST API** — Full-featured command-line interface and FastAPI HTTP interface

## Validation

- **520 tests** — all passing
- **9/10** real-world sites scanned successfully
- **0 crashes** — zero unhandled exceptions
- **Deterministic output** — identical input produces identical output
- **Multi-OS build** — Ubuntu, macOS, Windows

## Installation

```bash
pip install aifme-scout
```

## Quick Start

```bash
# Scan a website
aifme-scout scan https://www.python.org

# Outputs: scan-result.json + report.md
```

## Links

- **GitHub:** https://github.com/SureshBabuoo7/aifme-scout
- **PyPI:** https://pypi.org/project/aifme-scout/
- **Documentation:** https://github.com/SureshBabuoo7/aifme-scout/blob/master/docs
- **License:** Apache 2.0

## Limitations

AIFME Scout OSS is intentionally scoped. It does not execute JavaScript, bypass anti-bot protection, or persist data. It is a static extraction toolkit. See the [Limitations](https://github.com/SureshBabuoo7/aifme-scout/blob/master/docs/LIMITATIONS.md) documentation for the complete honest list.

## Maintenance Mode

Scout OSS is in **maintenance mode** as of v1.0.0. Only P0/P1 bug fixes and security updates are accepted. Engineering focus has shifted to the AIFME Platform. Community contributions are still welcome.

---

We built Scout OSS to be the kind of tool we wish existed when we were doing competitive intelligence, SEO audits, and technology stack analysis. We hope you find it useful.
