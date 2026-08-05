# FAQ

## What is Scout OSS?

AIFME Scout OSS is a free, open-source, self-hosted tool that scans a URL and returns a structured, evidence-linked snapshot of a business's web presence, technology stack, and marketing signals. It provides both a CLI and a REST API, with output as a versioned JSON schema.

## How is it different from AIFME Platform?

Scout OSS performs the **Understand** step of the AIFME model and nothing past it. It has no persistent memory, no reasoning or decision logic, and no ability to act on a target's behalf. The AIFME Platform includes Remember, Reason, Decide, Execute, and Measure capabilities that are not part of this open-source project.

## Why is the Brain not included?

The Brain is part of the commercial AIFME Platform and is outside the scope of Scout OSS. Scout OSS is a standalone extraction toolkit. It does not depend on or include any Platform-internal components.

## What output formats are supported?

Scout OSS produces two output formats:
- **JSON** — Schema-validated, pretty-printed with stable key ordering
- **Markdown** — Deterministic reports preserving all section headings and evidence references

## How is the JSON Schema versioned?

The JSON Schema is versioned independently from the engine version. The current schema version is `1.0.0`, and the engine version is `1.0.0`. Schema changes follow the [SCHEMA_CHANGELOG.md](../SCHEMA_CHANGELOG.md).

## Can I use Scout OSS for commercial purposes?

Yes. Scout OSS is licensed under the [Apache License 2.0](../LICENSE), which permits commercial use, modification, distribution, and private use.

## What Python versions are supported?

Scout OSS requires Python 3.11 or higher. It is tested on Python 3.11 and 3.12.

## Is Scout OSS actively maintained?

Scout OSS is in **maintenance mode** as of v1.0.0. Only P0/P1 bug fixes and security updates are accepted. Engineering focus has shifted to the AIFME Platform. Community contributions are still welcome but will be reviewed against the maintenance criteria. See [MAINTENANCE.md](../MAINTENANCE.md) for details.

## Can I contribute new features?

Feature requests are not prioritized during maintenance mode unless they are explicitly required by AIFME. Bug fixes and security updates are welcome. See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## What if a site blocks the scanner?

If a site's `robots.txt` disallows crawling, Scout OSS returns `LIMITED` status (exit code 3). If a site uses anti-bot protection (Cloudflare, Imperva, Datadome, CAPTCHA), the scan completes but may return challenge pages instead of actual HTML. Both are expected behavior, not failures.

## Does Scout OSS execute JavaScript?

No. Scout OSS fetches static HTML only. Sites that rely entirely on client-side rendering will appear empty or incomplete. This is a deliberate design decision.

## How accurate is the technology detection?

Technology detection is rule-based and covers 20+ frameworks, CMS platforms, servers, analytics tools, and CSS frameworks. It works on approximately 91% of modern websites. Custom or internal frameworks may not be detected without explicit rules.

## How does evidence collection work?

Every extracted data point is normalized into an `evidenceItem` with a deterministic ID, provenance (DOM path, tag, original text), confidence level, and traceable source URL. The `evidence` array in the JSON output is the authoritative source for every derived claim in the report.

## What is the evidence confidence model?

Each evidence item has a `confidence` field: `high`, `medium`, or `low`. High confidence means the evidence was found in multiple locations or with strong rule matches. Medium confidence means a single source with reasonable certainty. Low confidence means heuristic or inferred evidence.

## How do I report a security vulnerability?

Do not open a public issue. Email security@aifme.com with a description of the vulnerability, steps to reproduce, potential impact, and suggested fix. See [SECURITY.md](../SECURITY.md) for the full security policy.

## Where can I ask questions?

For general questions and discussions, use [GitHub Discussions](https://github.com/SureshBabuoo7/aifme-scout/discussions). For bug reports, use [GitHub Issues](https://github.com/SureshBabuoo7/aifme-scout/issues).
