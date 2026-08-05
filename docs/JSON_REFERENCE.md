# JSON Reference

The JSON output (`scan-result.json`) is a versioned, schema-validated document that serves as the canonical machine-readable contract for AIFME Scout OSS.

## Schema Versioning

- `schema_version` is semver and independent of `engine_version`.
- Additive fields are allowed within a minor version.
- Field removal or type changes require a new major version and a new `schemas/v2/` directory.
- Consumers must ignore unknown fields rather than error on them.

Current schema version: `1.0.0`  
Current engine version: `1.0.0`

## Top-Level Shape

```json
{
  "meta": { ... },
  "site": { ... },
  "seo": [ ... ],
  "metadata": [ ... ],
  "technology": [ ... ],
  "content": [ ... ],
  "social": [ ... ],
  "competitors": [ ... ],
  "evidence": [ ... ],
  "diagnostics": { ... }
}
```

## Field Reference

### `meta`

Schema and engine metadata.

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | `string` | Semver schema version. |
| `engine_version` | `string` | Semver engine version. |
| `timestamp` | `string` | ISO-8601 UTC timestamp of when the scan was executed. |

### `site`

Target site identifiers.

| Field | Type | Description |
|-------|------|-------------|
| `url` | `string` | Canonical target URL. |
| `target_url` | `string` | Original target URL supplied by the user. |

### `seo`

Evidence items derived from on-page SEO signals. Each item is an [`evidenceItem`](#evidenceitem).

### `metadata`

Evidence items derived from structured head metadata. Each item is an [`evidenceItem`](#evidenceitem).

### `technology`

Evidence items for detected technology fingerprints. Each item is an [`evidenceItem`](#evidenceitem).

### `content`

Evidence items extracted from readable body content. Each item is an [`evidenceItem`](#evidenceitem).

### `social`

Evidence items for discovered social profile links. Each item is an [`evidenceItem`](#evidenceitem).

### `competitors`

Evidence items for resolved competitors. Each item is an [`evidenceItem`](#evidenceitem).

### `evidence`

Complete flat list of all evidence items across every section above. This is the authoritative source for every derived claim in the scan.

### `diagnostics`

Build-time diagnostics and counters.

| Field | Type | Description |
|-------|------|-------------|
| `total_evidence_items` | `integer` | Total evidence items across all sections. |
| `seo_items` | `integer` | Number of SEO evidence items. |
| `metadata_items` | `integer` | Number of metadata evidence items. |
| `technology_items` | `integer` | Number of technology evidence items. |
| `content_items` | `integer` | Number of content evidence items. |
| `social_items` | `integer` | Number of social evidence items. |
| `competitor_items` | `integer` | Number of competitor evidence items. |
| `build_timestamp` | `string` | ISO-8601 UTC timestamp when the schema was built. |
| `scan_status` | `string` | Overall scan status label (e.g., `PASS`, `LIMITED`, `NO_DATA`). |
| `scan_coverage` | `number` | Overall scan coverage percentage (0–100). |

## `evidenceItem`

The fundamental unit of extracted data.

```json
{
  "evidence_id": "ev-000001",
  "evidence_type": "SEO_TITLE",
  "extractor_source": "seo",
  "value": "Python.org",
  "provenance": { ... },
  "confidence": "high",
  "page_url": "https://www.python.org",
  "timestamp": "2026-08-05T07:14:26+00:00",
  "attributes": {}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `evidence_id` | `string` | Deterministic unique identifier. |
| `evidence_type` | `string` | Machine-readable type label (e.g., `SEO_TITLE`, `TECHNOLOGY`). |
| `extractor_source` | `string` | The extractor module that produced this item. |
| `value` | `any` | The extracted value. Type varies by `evidence_type`. |
| `provenance` | [`evidenceProvenance`](#evidenceprovenance) | Source provenance. |
| `confidence` | `string` | One of `high`, `medium`, `low`. |
| `page_url` | `string` | URL where this evidence was found. |
| `timestamp` | `string` | ISO-8601 UTC timestamp. |
| `attributes` | `object` | Additional extractor-specific attributes. |

## `evidenceProvenance`

Traceability information for an evidence item.

```json
{
  "page_url": "https://www.python.org",
  "dom_path": "/html/body/h1",
  "tag": "h1",
  "attribute": null,
  "original_text": "Welcome to Python.org",
  "original_url": null,
  "detection_rule": null,
  "source": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `page_url` | `string` | URL where the evidence was found. |
| `dom_path` | `string \| null` | DOM path to the source element. |
| `tag` | `string \| null` | HTML tag name of the source element. |
| `attribute` | `string \| null` | HTML attribute name. |
| `original_text` | `string \| null` | Original text snippet. |
| `original_url` | `string \| null` | Original URL from the element. |
| `detection_rule` | `string \| null` | Rule or pattern that triggered detection. |
| `source` | `string \| null` | External source reference. |

## Extension Fields

The schema allows additional properties at the top level. Community-contributed extractors should namespace their output under an `extensions` object to avoid colliding with core fields.

## Validation

Every `ScanResult` produced by the Schema Builder is validated against `schemas/v1/scan-result.schema.json` before being returned. A validation failure is an engineering defect caught in CI, never a runtime user-facing error.

## Deterministic Output

- Key order is stable across runs (Python dict insertion order).
- Evidence IDs are deterministic for identical input.
- Sorting is applied where ordering matters (sitemap pages, evidence items).
- Timestamps and dynamic HTTP headers (e.g., Cloudflare `cf-ray`) are expected to vary between runs.

## See Also

- [Schema](schema.md) — Complete schema documentation
- [Report Reference](REPORT_REFERENCE.md) — Markdown report structure
- [Examples](../examples/) — Sample JSON outputs for real websites
- [CLI Reference](CLI_REFERENCE.md) — Output file options
