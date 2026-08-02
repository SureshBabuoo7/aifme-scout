# API Guide

This document describes the public APIs for AIFME Scout OSS.

## Mode Flag

Scout OSS supports two summary-generation modes:

- `no-llm` (default): produces a deterministic, template-based evidence-linked
  summary. Zero network calls beyond the target site.
- `llm`: attempts LLM-backed summary generation. Falls back to `no-llm` template
  mode when no provider is available.

The `mode` field is part of the `ScanRequest` payload and is resolved per
Architecture §5 Configuration precedence.

## JSON Exporter

The JSON Exporter converts a validated `ScoutSchema` into a stable JSON string
or file.

```python
from aifme_scout.exporters import export, export_to_file

# In-memory export
json_output = export(schema)

# File export
export_to_file(schema, Path("output/scan-result.json"))
```

Both functions are deterministic and thread-safe. `export_to_file` writes
UTF-8 encoded content and raises `OSError` on write failures.

## Request Handler

The Request Handler is the single entry point for both CLI and REST API
invocations. It validates the request, resolves configuration, orchestrates
the pipeline stage sequence, and assembles the final result.

```python
from aifme_scout.engine.request_handler import handle
from aifme_scout.utils.models import ScanRequest

request = ScanRequest(target_url="https://example.com")
result = handle(request)
```

### ScanRequest

| Field | Type | Description |
|---|---|---|
| `target_url` | `string` | The URL to scan. |
| `competitor_urls` | `string[]` | Optional competitor URLs. |
| `mode` | `ScanMode` | Summary generation mode (`no-llm` or `llm`). |
| `options` | `ScanOptions` | Scan options (crawl delay, max pages). |

### ScanResult

| Field | Type | Description |
|---|---|---|
| `meta` | `Meta` | Schema and engine metadata. |
| `target` | `Website` | Target website information. |
| `competitors` | `Website[]` | Discovered competitors. |
| `evidence` | `Evidence[]` | Collected evidence items. |
| `summary` | `Summary` | Generated summary. |
| `observations` | `Observation[]` | Flagged gaps, risks, or signals. |
| `errors` | `ScanError[]` | Partial-failure records. |

## REST API

The REST API provides an HTTP interface to Scout OSS using FastAPI.
It reuses the existing `RequestHandler.handle()` for pipeline orchestration.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | API documentation links |
| `GET` | `/health` | Health check |
| `GET` | `/version` | Version information |
| `POST` | `/scan` | Scan a website |

### Scan Request

```json
{
  "url": "https://example.com",
  "output": "both",
  "timeout": 10.0,
  "user_agent": "AIFME-Scout-OSS/1.0.0-rc1",
  "mode": "no-llm"
}
```

### Scan Response

Returns a `ScanResult` object with the assembled scan output.

### Interactive Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Markdown Exporter

The Markdown Exporter converts a `ScoutSummary` into a deterministic Markdown
document. It renders the summary text exactly as produced by the Summary
Builder; it does not summarize, infer, classify, or modify content.

```python
from aifme_scout.exporters import export_markdown, export_markdown_to_file

# In-memory export
markdown_output = export_markdown(summary)

# File export
export_markdown_to_file(summary, Path("output/report.md"))
```

### Rendering Rules

- Section headings, wording, and evidence references are preserved exactly.
- No additional text is injected.
- The output is UTF-8 encoded.
- File output ends with a trailing newline.

### Export API

| Function | Signature | Description |
|---|---|---|
| `export_markdown` | `export_markdown(summary: Summary) -> str` | Render summary to Markdown string |
| `export_markdown_to_file` | `export_markdown_to_file(summary, path) -> None` | Render summary and write to file |

Both functions are deterministic, stateless, and thread-safe.
