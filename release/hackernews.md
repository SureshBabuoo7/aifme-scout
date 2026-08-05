# Hacker News Post

Title: AIFME Scout OSS 1.0.0 – Open-source website and marketing intelligence toolkit

URL: https://github.com/SureshBabuoo7/aifme-scout

Text:

We released AIFME Scout OSS v1.0.0, a free and open-source Python toolkit that scans a URL and produces a structured, evidence-linked snapshot of a website's technology stack, SEO signals, content, metadata, social profiles, and competitor references.

It outputs a versioned JSON schema and a Markdown report, and exposes both a CLI and a REST API.

The project passed validation against 10 real-world sites (9 pass, 1 limited due to robots.txt, 0 failures) with 520 tests passing and zero crashes.

Key features:
- Safe scanning with SSRF protection, robots.txt awareness, retry logic
- 11 deterministic business classifications with confidence scores
- Technology detection (20+ frameworks, CMS, servers, security headers)
- SEO extraction (titles, meta, Open Graph, Twitter Cards, hreflang, AMP)
- Evidence-linked reports with provenance tracking
- Deterministic output (identical input → identical output)

It's Apache 2.0 licensed. Install with `pip install aifme-scout`.

The project is in maintenance mode (P0/P1 fixes + security only), but the codebase is fully functional and ready for use or extension.

Happy to answer questions.
