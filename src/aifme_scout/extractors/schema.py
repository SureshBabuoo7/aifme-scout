"""Schema Builder module.

Converts normalized EvidenceCollection into the canonical Scout OSS schema.
Validates the assembled schema against the published JSON Schema before
returning.
"""

from __future__ import annotations

import importlib.resources
import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from aifme_scout.extractors.models import (
    EvidenceCollection,
    EvidenceItem,
    ScoutMeta,
    ScoutSchema,
    ScoutSite,
)

if TYPE_CHECKING:
    pass


_SCHEMA_VERSION = "1.0.0"
_ENGINE_VERSION = "1.0.0"
_SCHEMA_RESOURCE = ("schemas", "v1", "scan-result.schema.json")


def _utc_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(UTC).isoformat()


def _to_serializable(value: Any) -> Any:
    """Convert a value to a JSON-serializable form."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list):
        return [_to_serializable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_serializable(v) for k, v in value.items()}
    if is_dataclass(value):
        return _to_serializable(asdict(value))  # type: ignore[arg-type]
    return str(value)


def _dataclass_to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass to a plain dict."""
    if is_dataclass(obj):
        return {k: _to_serializable(v) for k, v in asdict(obj).items()}  # type: ignore[arg-type]
    if isinstance(obj, list):
        return [_dataclass_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    return _to_serializable(obj)


def _load_schema() -> dict[str, Any]:
    """Load the canonical JSON Schema from package resources."""
    data = importlib.resources.files("aifme_scout").joinpath(*_SCHEMA_RESOURCE).read_text(encoding="utf-8")
    return json.loads(data)  # type: ignore[no-any-return]


def validate(schema_obj: ScoutSchema) -> None:
    """Validate a ScoutSchema against the published JSON Schema.

    Args:
        schema_obj: The assembled ScoutSchema to validate.

    Raises:
        jsonschema.ValidationError: If the schema object does not conform.
    """
    import jsonschema  # noqa: PLC0415  # type: ignore[import-untyped]

    schema_dict = _load_schema()
    data = _dataclass_to_dict(schema_obj)
    jsonschema.validate(instance=data, schema=schema_dict)


def _group_by_section(items: list[EvidenceItem]) -> dict[str, list[EvidenceItem]]:
    """Group evidence items by schema section."""
    sections: dict[str, list[EvidenceItem]] = {
        "seo": [],
        "metadata": [],
        "technology": [],
        "content": [],
        "social": [],
        "competitors": [],
    }

    seo_types = {
        "SEO_TITLE", "META_DESCRIPTION", "CANONICAL", "ROBOTS", "CHARSET",
        "VIEWPORT", "LANGUAGE", "OPEN_GRAPH", "TWITTER_CARD", "STRUCTURED_DATA",
        "INDEXABILITY",
    }
    metadata_types = {
        "SITE_NAME", "APPLICATION_NAME", "GENERATOR", "AUTHOR", "PUBLISHER",
        "COPYRIGHT", "THEME_COLOR", "COLOR_SCHEME", "FAVICON", "APPLE_TOUCH_ICON",
        "MANIFEST", "RSS_FEED", "ATOM_FEED", "ALTERNATE_LINK", "VERIFICATION_TAG",
        "WEB_APP_CAPABLE", "MOBILE_WEB_APP_CAPABLE",
    }
    technology_types = {"TECHNOLOGY"}
    content_types = {
        "CONTENT_HEADING", "CONTENT_PARAGRAPH", "CONTENT_LIST", "CONTENT_TABLE",
        "IMAGE", "LINK", "BUTTON", "FORM", "BREADCRUMB", "CONTENT_FOOTER",
    }
    social_types = {"SOCIAL_PROFILE"}
    competitor_types = {"COMPETITOR"}

    for item in items:
        if item.evidence_type in seo_types:
            sections["seo"].append(item)
        elif item.evidence_type in metadata_types:
            sections["metadata"].append(item)
        elif item.evidence_type in technology_types:
            sections["technology"].append(item)
        elif item.evidence_type in content_types:
            sections["content"].append(item)
        elif item.evidence_type in social_types:
            sections["social"].append(item)
        elif item.evidence_type in competitor_types:
            sections["competitors"].append(item)

    return sections


def _sort_key(item: EvidenceItem) -> tuple[str, ...]:
    """Return a stable sort key for deterministic ordering."""
    return (
        item.evidence_type,
        item.extractor_source,
        item.page_url,
        str(item.value),
        item.provenance.page_url,
        item.provenance.dom_path or "",
        item.provenance.tag or "",
        item.provenance.attribute or "",
        item.provenance.original_text or "",
        item.provenance.original_url or "",
        item.provenance.detection_rule or "",
        item.provenance.source or "",
        item.evidence_id,
    )


def build(evidence_collection: EvidenceCollection) -> ScoutSchema:
    """Build the canonical Scout OSS schema from an EvidenceCollection.

    This is the single point where raw extractor outputs are organized into
    the versioned schema. All downstream consumers should use this schema
    rather than reading extractor outputs directly.

    Args:
        evidence_collection: Normalized evidence from the Evidence Collector.

    Returns:
        ScoutSchema with organized sections.

    Raises:
        jsonschema.ValidationError: If the assembled schema does not validate
            against the published JSON Schema.
    """
    target_url = evidence_collection.target_url
    timestamp = _utc_timestamp()

    sorted_items = sorted(evidence_collection.items, key=_sort_key)
    sections = _group_by_section(sorted_items)

    seo_count = len(sections["seo"])
    metadata_count = len(sections["metadata"])
    technology_count = len(sections["technology"])
    content_count = len(sections["content"])
    social_count = len(sections["social"])
    competitors_count = len(sections["competitors"])

    diagnostics = {
        "total_evidence_items": len(sorted_items),
        "seo_items": seo_count,
        "metadata_items": metadata_count,
        "technology_items": technology_count,
        "content_items": content_count,
        "social_items": social_count,
        "competitor_items": competitors_count,
        "build_timestamp": timestamp,
    }

    schema_obj = ScoutSchema(
        meta=ScoutMeta(
            schema_version=_SCHEMA_VERSION,
            engine_version=_ENGINE_VERSION,
            timestamp=timestamp,
        ),
        site=ScoutSite(url=target_url, target_url=target_url),
        seo=sections["seo"],
        metadata=sections["metadata"],
        technology=sections["technology"],
        content=sections["content"],
        social=sections["social"],
        competitors=sections["competitors"],
        evidence=sorted_items,
        diagnostics=diagnostics,
    )

    validate(schema_obj)

    return schema_obj
