# TRANSITION TO AIFME PLATFORM

**Date:** 2026-08-06  
**Status:** Scout OSS Frozen — Platform Active

---

## Why Scout OSS is Frozen

AIFME Scout OSS has reached its intended endpoint: a stable, production-ready, open-source foundation for deterministic website intelligence.

Scout OSS was never designed to be a standalone product. It implements the **Understand** step of the AIFME model — the foundational data collection layer. The remaining steps (Remember, Reason, Decide, Execute, Measure) require capabilities that go beyond static extraction:

- **Remember** — Persistent memory, scan history, trend analysis
- **Reason** — LLM-backed analysis, recommendation generation, context-aware interpretation
- **Decide** — Automated decision-making, prioritization, action triggers
- **Execute** — Action execution on behalf of the user, integrations, workflows
- **Measure** — Outcome tracking, ROI measurement, business impact analysis

These capabilities require a commercial platform with managed infrastructure, user accounts, billing, and enterprise support. Scout OSS will remain available as the open-source entry point, but new capabilities will be built on the AIFME Platform.

---

## What Problems Scout OSS Solves

Scout OSS solves the problem of **structured website intelligence without vendor lock-in**:

- Deterministic, evidence-linked extraction from any public URL
- No AI required — rule-based detection that is explainable and auditable
- Self-hosted — run it anywhere, no external API calls for extraction
- Open source — inspect the code, modify the rules, extend the schema
- Schema-validated — versioned JSON output that integrates with any downstream system

Scout OSS is ideal for:
- Competitive intelligence analysts who need structured data
- SEO auditors who want reproducible, evidence-backed reports
- Developers building internal tools that need website intelligence
- Researchers collecting web data at scale
- Organizations with data residency or compliance requirements

---

## What Limitations are Intentional

Scout OSS is intentionally scoped. These are not bugs — they are design decisions:

- **No JavaScript execution** — Static HTML only. Sites requiring client-side rendering will appear empty. This is a feature, not a bug: it ensures deterministic, reproducible output.
- **No persistent memory** — Each scan is independent. No history, no comparisons across runs. This keeps Scout OSS stateless and simple.
- **No reasoning or decision logic** — Scout OSS extracts and classifies. It does not act on a target's behalf. This separation keeps the tool focused and auditable.
- **Technology detection is rule-based** — Custom or internal frameworks may not be detected without explicit rules. This is a trade-off for transparency and determinism.
- **Anti-bot protection is respected** — Cloudflare, Imperva, Datadome, and CAPTCHA challenges are detected and reported, not bypassed. Scout OSS will not help you do anything unethical or illegal.

These limitations ensure Scout OSS remains:
- **Deterministic** — Same input always produces same output
- **Explainable** — Every claim traces to a deterministic evidence item
- **Auditable** — No hidden logic, no black-box AI
- **Ethical** — Respects robots.txt, does not bypass protections

---

## Relationship Between Scout and AIFME Platform

```
┌─────────────────────────────────────────────────────────────┐
│                     AIFME Platform                           │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ ┌───────┐ ┌─────────┐ │
│  │Remember │ │ Reason  │ │ Decide │ │Execute│ │ Measure │ │
│  └────┬────┘ └────┬────┘ └───┬────┘ └───┬───┘ └────┬────┘ │
│       │           │          │           │            │     │
│  ─────┼───────────┼──────────┼───────────┼────────────┼──── │
│       │           │          │           │            │     │
│  ┌────▼───────────▼──────────▼───────────▼────────────▼────┐ │
│  │                  AIFME Orchestration Layer                │ │
│  └───────────────────────┬──────────────────────────────────┘ │
│                          │ uses                              │
│  ┌───────────────────────▼──────────────────────────────────┐ │
│  │              AIFME Scout OSS (Understand)                 │ │
│  │  • Deterministic extraction                               │ │
│  │  • Evidence-linked output                                 │ │
│  │  • Schema-validated JSON                                  │ │
│  │  • Self-hosted, open-source                               │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

Scout OSS is the **Understand** layer of the AIFME Platform. It is the open-source foundation that provides deterministic, evidence-linked website intelligence.

The AIFME Platform builds on top of Scout OSS by adding:
- Persistent memory and scan history
- LLM-backed analysis and recommendations
- Automated decision-making and action execution
- Outcome tracking and ROI measurement
- Multi-tenant SaaS with managed infrastructure
- Enterprise support and SLAs

Scout OSS users can migrate to the AIFME Platform when they need capabilities beyond static extraction. The JSON schema is compatible, so existing Scout OSS output can be ingested by the platform.

---

## How Scout Feeds the Commercial Platform

Scout OSS serves as the **data ingestion layer** for the AIFME Platform:

1. **Scout OSS** scans a URL and produces `scan-result.json` + `report.md`
2. **AIFME Platform** ingests the JSON output via API or file upload
3. **Platform** enriches the data with:
   - Historical scan data (Remember)
   - LLM analysis and recommendations (Reason)
   - Automated workflows and actions (Decide, Execute)
   - Business metrics and ROI tracking (Measure)

This architecture ensures:
- **No duplication** — Scout OSS does the extraction; the platform does the intelligence
- **Compatibility** — Scout OSS JSON schema is a subset of the platform's data model
- **Transparency** — Users can inspect exactly what Scout OSS extracted before the platform adds its layer
- **Portability** — Scout OSS output can be used with any downstream system, not just the AIFME Platform

---

## Future Roadmap

### Scout OSS (Maintenance Mode)

- Bug fixes (P0/P1 only)
- Security updates
- Python compatibility updates
- Documentation corrections

**No new features will be added to Scout OSS.**

### AIFME Platform (Active Development)

- Remember — Persistent memory and scan history
- Reason — LLM-backed analysis and recommendations
- Decide — Automated decision-making
- Execute — Action execution and integrations
- Measure — Outcome tracking and ROI measurement
- Multi-tenant SaaS with managed infrastructure
- Enterprise support and SLAs

---

## Engineering Philosophy

Scout OSS embodies a specific engineering philosophy:

1. **Determinism over magic** — Rule-based extraction that produces identical output for identical input
2. **Transparency over convenience** — Every claim traces to a deterministic evidence item with provenance
3. **Focused scope over feature creep** — Does one thing well: structured website intelligence
4. **Open source over lock-in** — Self-hosted, inspectable, extensible
5. **Ethical over powerful** — Respects robots.txt, does not bypass anti-bot protection

The AIFME Platform extends this philosophy with:
- **AI augmentation** — LLMs for analysis and recommendation
- **Action** — Execute decisions on behalf of the user
- **Memory** — Track changes over time
- **Scale** — Managed infrastructure for enterprise workloads

---

## Commercial Strategy

AIFME's commercial strategy is built on a **open-core model**:

- **Scout OSS** — Free, open-source, self-hosted, maintenance mode
- **AIFME Platform** — Commercial SaaS with advanced capabilities

Scout OSS serves as:
- **Lead generation** — Users try Scout OSS, outgrow it, migrate to platform
- **Trust building** — Open source demonstrates technical competence and transparency
- **Data ingestion** — Scout OSS output is compatible with platform input
- **Community** — Developers extend Scout OSS, some become platform customers

The platform monetizes through:
- SaaS subscriptions (tiered by usage and features)
- Enterprise support and SLAs
- Managed infrastructure (no self-hosting required)
- Advanced features (LLM analysis, action execution, memory)

---

## Developer Ecosystem Strategy

AIFME supports a developer ecosystem through:

1. **Scout OSS** — Free, open-source foundation for website intelligence
2. **JSON Schema** — Versioned, stable schema for integration
3. **CLI + REST API** — Multiple integration points
4. **Plugin system (future)** — Community-contributed extractors via formal plugin API (deferred to platform)
5. **Documentation** — Comprehensive guides for installation, usage, and extension
6. **Community** — GitHub Discussions for support and feature requests

Developers can:
- Use Scout OSS as a library in their own projects
- Extend Scout OSS with custom extractors (within maintenance constraints)
- Build integrations on top of the JSON output
- Contribute bug fixes and documentation improvements

For advanced capabilities (LLM analysis, action execution, memory), developers are directed to the AIFME Platform.

---

## Conclusion

AIFME Scout OSS v1.0.0 is a complete, stable, production-ready open-source project. It has served its purpose as the foundational layer of the AIFME Platform.

Future engineering effort will focus on the AIFME Platform, with Scout OSS maintained only for bug fixes, security updates, compatibility, and documentation.

Scout OSS will remain available indefinitely under the Apache 2.0 license. It is not deprecated — it is complete.

---

**Document:** TRANSITION_TO_AIFME_PLATFORM.md  
**Date:** 2026-08-06  
**Status:** Active
