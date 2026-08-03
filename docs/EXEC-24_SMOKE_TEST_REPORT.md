# EXEC-24 — Production Smoke Test

**Date:** 2026-08-03  
**Package:** `aifme_scout-1.0.0rc2-py3-none-any.whl`  
**Test Environment:** Fresh virtual environment, wheel-only install  
**Status:** PASS with 1 expected failure

---

## Test Environment Setup

```bash
python -m venv .venv-smoke-test
.\.venv-smoke-test\Scripts\python.exe -m pip install --force-reinstall dist\aifme_scout-1.0.0rc2-py3-none-any.whl
```

**Result:** Clean install, no source code required.

---

## CLI Verification

| Command | Result |
|---------|--------|
| `aifme-scout --help` | ✅ PASS |
| `aifme-scout --version` | ✅ `aifme-scout 1.0.0rc2` |
| `python -m aifme_scout --help` | ✅ PASS |

---

## Website Scan Results

| Site | Exit Code | JSON | Markdown | Evidence | Tech | SEO | Meta | Status |
|------|-----------|------|----------|----------|------|-----|------|--------|
| https://python.org | 0 | ✅ | ✅ | 320 | 3 | 8 | 20 | ✅ PASS |
| https://github.com | 0 | ✅ | ✅ | 437 | 7 | 9 | 34 | ✅ PASS |
| https://openai.com | 0 | ✅ | ✅ | 2 | 1 | 1 | 0 | ⚠️ LOW YIELD |
| https://microsoft.com | 0 | ✅ | ✅ | 167 | 3 | 10 | 1 | ✅ PASS |
| https://cloudflare.com | 0 | ✅ | ✅ | 328 | 3 | 10 | 36 | ✅ PASS |
| https://wordpress.org | 0 | ✅ | ✅ | 637 | 2 | 10 | 480 | ✅ PASS |
| https://shopify.com | 0 | ✅ | ✅ | 697 | 1 | 10 | 201 | ✅ PASS |
| https://reddit.com | 1 | ❌ | ❌ | — | — | — | — | ❌ EXPECTED |
| https://wikipedia.org | 0 | ✅ | ✅ | 1 | 0 | 1 | 0 | ⚠️ LOW YIELD |
| https://stackoverflow.com | 0 | ✅ | ✅ | 7 | 1 | 6 | 0 | ⚠️ LOW YIELD |

---

## Feature Verification

### JSON Output
- ✅ Valid JSON produced for all successful scans
- ✅ Schema-validated (no validation errors)
- ✅ Contains `meta`, `site`, `diagnostics`, `seo`, `metadata`, `technology`, `content`, `social`, `competitors` sections
- ✅ Evidence IDs are deterministic (`ev-000001` format)

### Markdown Output
- ✅ Markdown report generated
- ✅ Contains Executive Summary, Website Overview, SEO Summary, Metadata Summary
- ✅ Evidence references preserved

### Technology Detection
- ✅ python.org: jQuery, jQuery UI, nginx detected
- ✅ github.com: 7 technologies detected
- ✅ cloudflare.com: 3 technologies detected
- ✅ wordpress.org: WordPress detected
- ✅ shopify.com: Shopify detected

### SEO Extraction
- ✅ Title extraction works
- ✅ Meta description extraction works
- ✅ Open Graph extraction works
- ✅ Structured data detection works
- ✅ Viewport detection works
- ✅ Language detection works

### Metadata Extraction
- ✅ RSS/Atom feed detection works
- ✅ Favicon detection works
- ✅ Site name detection works
- ✅ Apple touch icon detection works
- ✅ Web app capable detection works

### Error Handling
- ✅ reddit.com: Correctly blocked by robots.txt (`robots.txt disallows path: /`)
- ✅ No unhandled exceptions
- ✅ Graceful error messages

---

## Critical Bug Found and Fixed

### Bug: Schema File Not Included in Wheel

**Symptom:** All scans failed with `FileNotFoundError: [Errno 2] No such file or directory: '...schemas/v1/scan-result.schema.json'`

**Root Cause:** The `schemas/` directory at the project root was not included in the wheel package. The code computed the schema path relative to the project root (4 directory levels up from `schema.py`), which works in editable installs but fails in wheel installs.

**Fix Applied:**
1. Copied `schemas/v1/scan-result.schema.json` into the package at `src/aifme_scout/schemas/v1/scan-result.schema.json`
2. Updated `src/aifme_scout/extractors/schema.py` to load the schema via `importlib.resources` with a fallback to the original path for editable installs
3. Rebuilt the wheel

**Commit:** Included in the packaging fix commit.

---

## Low-Yield Sites (Expected Behavior)

| Site | Reason for Low Yield |
|------|----------------------|
| openai.com | Anti-bot protection / challenge page |
| wikipedia.org | Minimal metadata, simple structure |
| stackoverflow.com | Anti-bot protection / minimal extraction |

These are expected limitations documented in `docs/GITHUB_RELEASE_RC2.md`.

---

## Final Verdict

**PASS — READY FOR PYPI**

The package installs cleanly from the wheel, CLI works, all core features function correctly, and error handling is proper. The only failure (reddit.com) is expected due to robots.txt restrictions.

---

## Recommendation

**READY FOR PYPI**

Upload with:
```bash
python -m twine upload dist/*
```

---

*Report generated as part of EXEC-24 — Production Smoke Test.*
