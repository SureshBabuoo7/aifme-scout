# Schema

Scout OSS produces a versioned `ScanResult` object for every scan. The canonical
machine-readable contract is `schemas/v1/scan-result.schema.json`.

## Versioning

- `schema_version` is semver and independent of `engine_version`.
- Additive fields are allowed within a minor version.
- Field removal or type changes require a new major version and a new
  `schemas/v2/` directory per Architecture §8/§17.
- Consumers must ignore unknown fields rather than error on them.

## Top-Level Shape

```json
{
  "meta": { ... },
  "site": { ... },
  "seo": [ ... ],
  "metadata": [ ... ],
  "technology": [ ... ],
  "content": [ ... },
  "social": [ ... ],
  "competitors": [ ... ],
  "evidence": [ ... ],
  "diagnostics": { ... }
}
```

### `meta`

Schema and engine metadata.

| Field | Type | Description |
|---|---|---|
| `schema_version` | `string` | Semver schema version. |
| `engine_version` | `string` | Semver engine version. |
| `timestamp` | `string` | ISO-8601 UTC timestamp of when the schema was built. |

### `site`

Target site identifiers.

| Field | Type | Description |
|---|---|---|
| `url` | `string` | Canonical target URL. |
| `target_url` | `string` | Original target URL supplied by the user. |

### `seo`

Evidence items derived from on-page SEO signals. Each item is an
[`evidenceItem`](#evidenceitem).

### `metadata`

Evidence items derived from structured head metadata (Open Graph, Twitter Card,
schema.org, favicon, language, etc.). Each item is an
[`evidenceItem`](#evidenceitem).

### `technology`

Evidence items for detected technology fingerprints. Each item is an
[`evidenceItem`](#evidenceitem).

### `content`

Evidence items extracted from readable body content (headings, paragraphs,
lists, tables, images, links, etc.). Each item is an
[`evidenceItem`](#evidenceitem).

### `social`

Evidence items for discovered social profile links. Each item is an
[`evidenceItem`](#evidenceitem).

### `competitors`

Evidence items for resolved competitors. Each item is an
[`evidenceItem`](#evidenceitem).

### `evidence`

Complete flat list of all evidence items across every section above. This is
the authoritative source for every derived claim in the scan.

### `diagnostics`

Build-time diagnostics and counters.

| Field | Type | Description |
|---|---|---|
| `total_evidence_items` | `integer` | Total evidence items across all sections. |
| `seo_items` | `integer` | Number of SEO evidence items. |
| `metadata_items` | `integer` | Number of metadata evidence items. |
| `technology_items` | `integer` | Number of technology evidence items. |
| `content_items` | `integer` | Number of content evidence items. |
| `social_items` | `integer` | Number of social evidence items. |
| `competitor_items` | `integer` | Number of competitor evidence items. |
| `build_timestamp` | `string` | ISO-8601 UTC timestamp when the schema was built. |

## `evidenceItem`

```json
{
  "evidence_id": "ev-000001",
  "evidence_type": "SEO_TITLE",
  "extractor_source": "seo",
  "value": "...",
  "provenance": { ... },
  "confidence": "high",
  "page_url": "https://example.com",
  "timestamp": "2024-01-01T00:00:00+00:00",
  "attributes": {}
}
```

| Field | Type | Description |
|---|---|---|
| `evidence_id` | `string` | Deterministic unique identifier. |
| `evidence_type` | `string` | Machine-readable type label (e.g. `SEO_TITLE`, `TECHNOLOGY`). |
| `extractor_source` | `string` | The extractor module that produced this item. |
| `value` | `any` | The extracted value. Type varies by `evidence_type`. |
| `provenance` | [`evidenceProvenance`](#evidenceprovenance) | Source provenance. |
| `confidence` | `string` | One of `high`, `medium`, `low`. |
| `page_url` | `string` | URL where this evidence was found. |
| `timestamp` | `string` | ISO-8601 UTC timestamp. |
| `attributes` | `object` | Additional extractor-specific attributes. |

## `evidenceProvenance`

```json
{
  "page_url": "https://example.com",
  "dom_path": "/html/body/h1",
  "tag": "h1",
  "attribute": null,
  "original_text": "Welcome",
  "original_url": null,
  "detection_rule": null,
  "source": null
}
```

| Field | Type | Description |
|---|---|---|
| `page_url` | `string` | URL where the evidence was found. |
| `dom_path` | `string \| null` | DOM path to the element. |
| `tag` | `string \| null` | HTML tag name of the source element. |
| `attribute` | `string \| null` | HTML attribute name. |
| `original_text` | `string \| null` | Original text snippet. |
| `original_url` | `string \| null` | Original URL from the element. |
| `detection_rule` | `string \| null` | Rule or pattern that triggered detection. |
| `source` | `string \| null` | External source reference. |

## Extension Fields

The schema allows additional properties at the top level. Community-contributed
extractors should namespace their output under an `extensions` object to avoid
colliding with core fields.

## Validation

Every `ScanResult` produced by the Schema Builder is validated against
`schemas/v1/scan-result.schema.json` before being returned. A validation failure
is an engineering defect caught in CI, never a runtime user-facing error.

## Summary Model

The Summary Builder converts a `ScoutSchema` into a deterministic,
evidence-linked descriptive summary. The summary is produced by the
`summarize` function in `src/engine/summary.py`.

```json
{
  "text": "## Executive Summary\nTarget site: https://example.com\n...",
  "evidence_refs": ["ev-000001", "ev-000002", "https://example.com"]
}
```

| Field | Type | Description |
|---|---|---|
| `text` | `string` | Markdown-formatted descriptive summary. |
| `evidence_refs` | `string[]` | Deduplicated evidence IDs and source URLs referenced in the summary. |

## Summary Sections

The summary is organized into the following sections, in this fixed order:

1. Executive Summary
2. Website Overview
3. SEO Summary
4. Metadata Summary
5. Technology Summary
6. Content Summary
7. Social Presence Summary
8. Competitor Summary
9. Diagnostics
10. Data Completeness

Each section is prefixed with a Markdown heading (`## Section Name`).

## Traceability Rules

- Every factual claim in the summary must trace to one or more evidence IDs
  present in the input `ScoutSchema`.
- Evidence references (`evidence_refs`) are preserved from the schema and
  deduplicated in the output summary.
- Source URLs from `EvidenceItem.page_url` and `ScoutSite.url` are included
  as traceable references.
- No evidence reference may be discarded during summary generation.

## Deterministic Summary Rules

- The summary is deterministic: identical input `ScoutSchema` produces
  identical output `Summary`.
- Section order is fixed and stable.
- Evidence references are deduplicated while preserving insertion order.
- The summary is stateless and thread-safe.
- No claim is invented, inferred, or guessed; every statement originates
  from collected evidence.

## JSON Export

The JSON Exporter serializes a `ScoutSchema` into a stable, pretty-printed JSON
document that conforms to `schemas/v1/scan-result.schema.json`.

```python
from aifme_scout.exporters import export, export_to_file

# Serialize to string
json_string = export(schema)

# Write to file
export_to_file(schema, "scan-result.json")
```

### Output Format

- UTF-8 encoded
- Pretty printed with 2-space indentation
- Stable alphabetical key ordering (`sort_keys=True`)
- Deterministic output for identical input
- No mutation of the input `ScoutSchema`

### Schema Compatibility

The exported JSON validates against `schemas/v1/scan-result.schema.json`.
No fields are added, removed, or modified during serialization.

### Export API

| Function | Signature | Description |
|---|---|---|
| `export` | `export(schema: ScoutSchema) -> str` | Serialize schema to JSON string |
| `export_to_file` | `export_to_file(schema, path) -> None` | Serialize schema and write to file |

The exporter is stateless and thread-safe.
