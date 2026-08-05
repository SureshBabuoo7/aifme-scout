"""Regenerate validation reports with the current code."""
from __future__ import annotations

import json
from pathlib import Path

from aifme_scout.exporters.markdown_exporter import export
from aifme_scout.extractors.models import ScoutSchema, ScoutMeta, ScoutSite
from aifme_scout.engine.summary import summarize
from aifme_scout.utils.models import Summary


ROOT = Path("validation_output")
SITES = ["python_org", "github_com", "cloudflare_com", "openai_com"]


def _load_schema(path: Path) -> ScoutSchema:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    meta_data = data.get("meta", {})
    site_data = data.get("site", {})
    meta = ScoutMeta(
        schema_version=meta_data.get("schema_version", "1.0.0"),
        engine_version=meta_data.get("engine_version", "1.0.0"),
        timestamp=meta_data.get("timestamp", ""),
    )
    site = ScoutSite(
        url=site_data.get("url", ""),
        target_url=site_data.get("target_url", site_data.get("url", "")),
    )

    def _load_items(items_data: list[dict]) -> list:
        items = []
        for item_data in items_data:
            prov = item_data.get("provenance", {})
            from aifme_scout.extractors.models import EvidenceItem, EvidenceProvenance
            items.append(EvidenceItem(
                evidence_id=item_data.get("evidence_id", ""),
                evidence_type=item_data.get("evidence_type", ""),
                extractor_source=item_data.get("extractor_source", ""),
                value=item_data.get("value"),
            provenance=EvidenceProvenance(
                page_url=prov.get("page_url", ""),
                dom_path=prov.get("dom_path"),
                tag=prov.get("tag"),
                attribute=prov.get("attribute"),
                original_text=prov.get("original_text"),
                original_url=prov.get("original_url"),
                detection_rule=prov.get("detection_rule"),
                source=prov.get("source"),
            ) if prov else None,
                confidence=item_data.get("confidence", "medium"),
                page_url=item_data.get("page_url", ""),
                timestamp=item_data.get("timestamp", ""),
            ))
        return items

    return ScoutSchema(
        meta=meta,
        site=site,
        seo=_load_items(data.get("seo", [])),
        metadata=_load_items(data.get("metadata", [])),
        technology=_load_items(data.get("technology", [])),
        content=_load_items(data.get("content", [])),
        social=_load_items(data.get("social", [])),
        competitors=_load_items(data.get("competitors", [])),
        evidence=_load_items(data.get("evidence", [])),
        diagnostics=data.get("diagnostics", {}),
    )


def main() -> None:
    for site in SITES:
        json_path = ROOT / site / "scan-result.json"
        report_path = ROOT / site / "report.md"
        if not json_path.exists():
            print(f"SKIP {site}: missing {json_path}")
            continue

        schema = _load_schema(json_path)
        summary: Summary = summarize(schema)
        markdown = export(summary)
        report_path.write_text(markdown, encoding="utf-8")
        print(f"OK {site}: wrote {report_path}")


if __name__ == "__main__":
    main()
