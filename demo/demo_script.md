# Demo Script

AIFME Scout OSS v1.0.0 — 3-Minute Demo

## Setup (Pre-Recorded)

1. Open terminal
2. Show clean environment:
   ```bash
   python --version
   # Python 3.11.x
   ```
3. Install:
   ```bash
   pip install aifme-scout
   ```

## Act 1: Basic Scan (0:00–0:45)

1. Run scan:
   ```bash
   aifme-scout scan https://www.python.org
   ```
2. Show output:
   ```
   [INFO] Scanning https://www.python.org
   [INFO] Fetched 1 page(s) in 2.5s
   [INFO] Collected 347 evidence items
   [INFO] Classification: Programming Language Documentation Portal (confidence: high)
   [INFO] Health Score: 85/100
   [INFO] Report written to report.md
   [INFO] JSON written to scan-result.json
   ```
3. Show generated files in terminal:
   ```bash
   ls -la
   # scan-result.json  report.md
   ```

## Act 2: Markdown Report (0:45–1:30)

1. Open `report.md` in editor or pager:
   ```bash
   cat report.md
   ```
2. Highlight sections:
   - Executive Summary with health score
   - Scan Limitations (transparent disclosure)
   - Website Classification
   - SEO Summary
   - Technology Summary
   - Social Presence
   - Diagnostics
3. Point out evidence-linked claims

## Act 3: JSON Output (1:30–2:15)

1. Show `scan-result.json`:
   ```bash
   cat scan-result.json | python -m json.tool | head -50
   ```
2. Highlight:
   - `meta.schema_version` — versioned schema
   - `diagnostics.total_evidence_items` — 347 evidence items
   - Evidence items with deterministic IDs (`ev-000001`)
   - Provenance fields (DOM path, tag, original text)

## Act 4: REST API (2:15–2:45)

1. Start API server:
   ```bash
   uvicorn aifme_scout.api.app:app --host 0.0.0.0 --port 8000
   ```
2. Open browser to http://localhost:8000/docs
3. Show Swagger UI
4. Execute `/scan` endpoint with `{"url": "https://www.python.org"}`
5. Show JSON response

## Closing (2:45–3:00)

1. Return to terminal
2. Show cleanup:
   ```bash
   rm scan-result.json report.md
   ```
3. Final message:
   ```
   AIFME Scout OSS v1.0.0
   pip install aifme-scout
   github.com/SureshBabuoo7/aifme-scout
   Apache 2.0
   ```

## Recording Tips

- Use a terminal with a clean, high-contrast theme
- Zoom terminal font to 14pt+ for readability
- Record at 1080p minimum, 60fps preferred
- Add subtle background music or keep it silent
- Add chapter markers for each act
- Show real scan output (use python.org for consistency)
