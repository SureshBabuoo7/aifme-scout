# Quick Start

Get up and running with AIFME Scout OSS in under 5 minutes.

## Prerequisites

- Python 3.11 or higher
- pip or compatible package manager

See [INSTALLATION.md](INSTALLATION.md) for platform-specific setup.

## Installation

```bash
pip install aifme-scout
```

## Your First Scan

```bash
aifme-scout scan https://www.python.org
```

That's it. Scout OSS will:

1. Fetch the target URL
2. Parse the HTML
3. Extract SEO, metadata, technology, content, social, and competitor signals
4. Assemble a validated JSON schema
5. Generate a Markdown executive report
6. Write `scan-result.json` and `report.md` to the current directory

## CLI Examples

### Basic Scan

```bash
aifme-scout scan https://www.python.org
```

### JSON Only

```bash
aifme-scout scan https://www.python.org --output json --out ./reports
```

### Markdown Only

```bash
aifme-scout scan https://www.python.org --output markdown --out ./reports
```

### Custom Timeout

```bash
aifme-scout scan https://www.python.org --timeout 30
```

### Quiet Mode (CI/CD Friendly)

```bash
aifme-scout scan https://www.python.org --quiet
```

### Verbose Mode (Debugging)

```bash
aifme-scout scan https://www.python.org --verbose
```

### Multiple Sites (Bash Loop)

```bash
for url in https://python.org https://openai.com https://github.com; do
  aifme-scout scan "$url" --out ./reports --quiet
done
```

## REST API

Start the server:

```bash
uvicorn aifme_scout.api.app:app --host 0.0.0.0 --port 8000
```

### Scan via cURL

```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.python.org"}'
```

### Scan via Python

```python
import httpx

response = httpx.post(
    "http://localhost:8000/scan",
    json={"url": "https://www.python.org"},
    timeout=30.0
)
result = response.json()
print(result["summary"]["text"])
```

## Python API

```python
from aifme_scout.engine.request_handler import handle
from aifme_scout.utils.models import ScanRequest

request = ScanRequest(
    target_url="https://www.python.org",
    competitor_urls=["https://example.com"],
    mode="no-llm"
)
result = handle(request)

# Access structured results
print(result.summary.text)
print(f"Evidence items: {result.summary.diagnostics.total_evidence_items}")
print(f"Classification: {result.summary.target_classification}")
```

## Output Files

| File | Format | Description |
|------|--------|-------------|
| `scan-result.json` | JSON | Schema-validated JSON report with all evidence items |
| `report.md` | Markdown | Executive intelligence report with health score and takeaways |

## Next Steps

- [CLI Reference](CLI_REFERENCE.md) — Full command reference
- [JSON Reference](JSON_REFERENCE.md) — JSON schema documentation
- [Report Reference](REPORT_REFERENCE.md) — Markdown report structure
- [Architecture](ARCHITECTURE.md) — System design and module overview
- [Examples](../examples/) — Real scan examples and interpretations
