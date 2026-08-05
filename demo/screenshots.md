# Screenshots Guide

This guide documents the screenshots required for the AIFME Scout OSS v1.0.0 launch.

## Required Screenshots

The following screenshots are referenced in the README and should be placed in `assets/screenshots/`:

| Screenshot | Description | Dimensions | Format |
|------------|-------------|------------|--------|
| `cli-output.png` | Terminal showing a basic scan with output | 1200×800 | PNG |
| `swagger-ui.png` | FastAPI Swagger UI showing `/scan` endpoint | 1200×800 | PNG |
| `json-output.png` | JSON report open in code editor | 1200×800 | PNG |
| `markdown-report.png` | Markdown report open in markdown viewer | 1200×800 | PNG |

## Screenshot Specifications

- **Resolution:** 1200×800 minimum (higher is better)
- **Format:** PNG with transparency where applicable
- **Theme:** Light theme preferred for maximum readability
- **Font:** System monospace font for terminal/code screenshots

## How to Capture

### CLI Output

```bash
# Run scan
aifme-scout scan https://www.python.org --quiet

# Take screenshot of terminal showing output
```

### Swagger UI

```bash
# Start API server
uvicorn aifme_scout.api.app:app --host 0.0.0.0 --port 8000

# Navigate to http://localhost:8000/docs
# Take screenshot
```

### JSON Output

```bash
# Generate report
aifme-scout scan https://www.python.org --output json

# Open scan-result.json in your editor
# Take screenshot
```

### Markdown Report

```bash
# Generate report
aifme-scout scan https://www.python.org --output markdown

# Open report.md in your markdown viewer
# Take screenshot
```

## Current Assets

The following assets already exist in the repository:

- `assets/logo.svg` — Project logo (vector)
- `assets/banner.svg` — Banner image (vector)
- `assets/banner.png` — Banner image (raster)
- `assets/screenshots/cli-output.png` — CLI output screenshot
- `assets/screenshots/swagger-ui.png` — Swagger UI screenshot
- `assets/screenshots/json-output.png` — JSON output screenshot
- `assets/screenshots/markdown-report.png` — Markdown report screenshot
- `assets/screenshots/markdown-report.html` — HTML version of markdown report (for rendering)

## Notes

- Screenshots should be updated whenever the UI or output format changes significantly
- The HTML file in `assets/screenshots/markdown-report.html` is a rendered version of the report for use in documentation
- All screenshots should be checked into git (not gitignored)
