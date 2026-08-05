# Limitations

AIFME Scout OSS is intentionally scoped. These are honest limitations, not bugs.

## Browser Limitations

- **No JavaScript execution** — Scout OSS fetches static HTML only. Sites that rely entirely on client-side rendering (SPA, SSR via JS frameworks) will appear empty or incomplete.
- **No browser rendering** — No headless browser, no Selenium, no Playwright. Scout OSS does not execute JavaScript, wait for network idle, or render CSS.
- **Dynamic content** — Content loaded via AJAX after initial page load will not be captured.

## Network Limitations

- **robots.txt is respected** — Sites that disallow crawling via `robots.txt` will return `LIMITED` status (exit code 3). This is expected behavior, not a failure.
- **Anti-bot protection is respected** — Cloudflare, Imperva, Datadome, and CAPTCHA challenges are detected and reported. Scout OSS will not bypass them.
- **Rate limiting** — Sites that return `429 Too Many Requests` will be reported with `RATE_LIMITED` evidence. Retry-After headers are honored where present.
- **Large sites** — Default maximum is 25 pages per scan. This is configurable but very large sites may time out or require multiple scans.
- **Slow sites** — Timeouts are configurable. Sites that take longer than the configured timeout will fail with a `TIMEOUT` error.

## Extraction Limitations

- **Technology detection is rule-based** — Custom or internal frameworks, proprietary platforms, and bleeding-edge libraries may not be detected without explicit rules.
- **SEO scoring is not included** — Scout OSS extracts SEO signals but does not score or grade them. That logic belongs in the AIFME Platform.
- **Content extraction is structural** — Scout OSS extracts headings, paragraphs, lists, tables, and other structural elements. It does not summarize, paraphrase, or interpret content.
- **Social discovery is link-based** — Social profiles are discovered from page links and JSON-LD markup. Profiles not linked from scanned pages will not be found.
- **Competitor discovery requires context** — Heuristic competitor discovery works best when the target's business classification is known. Without classification, results are limited to explicit "vs" and "alternatives" mentions.

## Architectural Limitations

- **No persistent memory** — Each scan is independent. No history, no comparisons across runs, no trend analysis.
- **No reasoning or decision logic** — Scout OSS extracts and classifies. It does not act on a target's behalf.
- **No authentication, persistence, rate limiting, or background jobs** — These are deferred by design. Scout OSS is a stateless extraction toolkit.
- **No plugin system** — Community extensions should use the `extensions` namespace in JSON output. No formal plugin API exists in v1.0.0.
- **Schema changes require migration** — The JSON Schema is versioned. Breaking schema changes require a new major version (`v2/`) and a migration guide.

## Maintenance Mode

Scout OSS is in **maintenance mode** as of v1.0.0. Only the following changes are accepted:

- **P0/P1 bug fixes** — Critical functionality that is broken or unusable
- **Security updates** — Vulnerabilities in dependencies or runtime behavior
- **AIFME-required changes** — Changes explicitly required by the AIFME platform team

No new features, enhancements, or refactoring will be accepted unless required by AIFME.

See [MAINTENANCE.md](MAINTENANCE.md) for the full maintenance policy.
