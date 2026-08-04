"""Unit tests for the Schema Builder module."""

from pathlib import Path

import pytest

from aifme_scout.extractors import (
    EvidenceCollection,
    EvidenceItem,
    EvidenceProvenance,
    build_schema,
    collect_evidence,
    validate_schema,
)
from aifme_scout.extractors.competitors import resolve as resolve_competitors
from aifme_scout.extractors.content import extract as extract_content
from aifme_scout.extractors.metadata import extract as extract_metadata
from aifme_scout.extractors.seo import analyze
from aifme_scout.extractors.social import discover as discover_social
from aifme_scout.extractors.technology import detect as detect_technology
from aifme_scout.parser import parse
from aifme_scout.scanner.models import RawPage, RawSite


def _make_evidence_item(
    evidence_id: str = "ev-000001",
    evidence_type: str = "SEO_TITLE",
    extractor_source: str = "seo",
    value: object = "Test Title",
    page_url: str = "https://example.com",
    confidence: str = "high",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        evidence_type=evidence_type,
        extractor_source=extractor_source,
        value=value,
        provenance=EvidenceProvenance(page_url=page_url),
        confidence=confidence,
        page_url=page_url,
        timestamp="2024-01-01T00:00:00+00:00",
    )


def _make_collection(items: list[EvidenceItem] | None = None) -> EvidenceCollection:
    if items is None:
        items = [_make_evidence_item()]
    return EvidenceCollection(target_url="https://example.com", items=items)


def _load_fixture(name: str) -> str:
    return Path("tests/fixtures/html").joinpath(name).read_text(encoding="utf-8")


def _parse(
    html: str, url: str = "https://example.com", headers: dict[str, str] | None = None
) -> RawSite:
    page = RawPage(
        url=url,
        final_url=url,
        status_code=200,
        headers=headers or {"content-type": "text/html"},
        html=html,
    )
    return RawSite(target_url=url, pages=[page], sitemap_urls=[])


class TestEmptyEvidence:
    def test_empty_collection_builds_schema(self) -> None:
        collection = _make_collection([])
        schema = build_schema(collection)
        assert schema.site.url == "https://example.com"
        assert schema.meta.schema_version == "1.0.0"
        assert schema.evidence == []

    def test_empty_collection_diagnostics(self) -> None:
        collection = _make_collection([])
        schema = build_schema(collection)
        assert schema.diagnostics["total_evidence_items"] == 0
        assert schema.diagnostics["seo_items"] == 0


class TestSchemaConstruction:
    def test_basic_schema_construction(self) -> None:
        collection = _make_collection()
        schema = build_schema(collection)
        assert schema.site.url == "https://example.com"
        assert schema.meta.schema_version == "1.0.0"
        assert schema.meta.engine_version == "1.0.0"
        assert schema.meta.timestamp is not None

    def test_schema_version_present(self) -> None:
        collection = _make_collection()
        schema = build_schema(collection)
        assert schema.meta.schema_version == "1.0.0"
        assert "." in schema.meta.schema_version


class TestEvidencePreservation:
    def test_evidence_preserved_in_schema(self) -> None:
        items = [_make_evidence_item(evidence_id="ev-000001", evidence_type="SEO_TITLE")]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert len(schema.evidence) == 1
        assert schema.evidence[0].evidence_id == "ev-000001"
        assert schema.evidence[0].evidence_type == "SEO_TITLE"

    def test_evidence_ids_preserved(self) -> None:
        items = [
            _make_evidence_item(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
            _make_evidence_item(evidence_id="ev-000002", evidence_type="META_DESCRIPTION"),
        ]
        collection = _make_collection(items)
        schema = build_schema(collection)
        ids = [item.evidence_id for item in schema.evidence]
        assert "ev-000001" in ids
        assert "ev-000002" in ids


class TestSectionGrouping:
    def test_seo_evidence_grouped(self) -> None:
        items = [_make_evidence_item(evidence_type="SEO_TITLE")]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert len(schema.seo) == 1
        assert schema.seo[0].evidence_type == "SEO_TITLE"

    def test_metadata_evidence_grouped(self) -> None:
        items = [_make_evidence_item(evidence_type="GENERATOR")]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert len(schema.metadata) == 1
        assert schema.metadata[0].evidence_type == "GENERATOR"

    def test_technology_evidence_grouped(self) -> None:
        items = [_make_evidence_item(evidence_type="TECHNOLOGY")]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert len(schema.technology) == 1
        assert schema.technology[0].evidence_type == "TECHNOLOGY"

    def test_content_evidence_grouped(self) -> None:
        items = [_make_evidence_item(evidence_type="CONTENT_HEADING")]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert len(schema.content) == 1
        assert schema.content[0].evidence_type == "CONTENT_HEADING"

    def test_social_evidence_grouped(self) -> None:
        items = [_make_evidence_item(evidence_type="SOCIAL_PROFILE")]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert len(schema.social) == 1
        assert schema.social[0].evidence_type == "SOCIAL_PROFILE"

    def test_competitor_evidence_grouped(self) -> None:
        items = [_make_evidence_item(evidence_type="COMPETITOR")]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert len(schema.competitors) == 1
        assert schema.competitors[0].evidence_type == "COMPETITOR"


class TestStableOrdering:
    def test_deterministic_ordering(self) -> None:
        items = [
            _make_evidence_item(evidence_id="ev-000002", evidence_type="META_DESCRIPTION"),
            _make_evidence_item(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
        ]
        collection = _make_collection(items)
        schema1 = build_schema(collection)
        schema2 = build_schema(collection)
        assert [item.evidence_id for item in schema1.evidence] == [
            item.evidence_id for item in schema2.evidence
        ]

    def test_sorted_by_type_then_id(self) -> None:
        items = [
            _make_evidence_item(evidence_id="ev-000002", evidence_type="META_DESCRIPTION"),
            _make_evidence_item(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
        ]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert schema.evidence[0].evidence_type == "META_DESCRIPTION"
        assert schema.evidence[1].evidence_type == "SEO_TITLE"


class TestMixedEvidence:
    def test_mixed_evidence_in_all_sections(self) -> None:
        items = [
            _make_evidence_item(evidence_type="SEO_TITLE"),
            _make_evidence_item(evidence_type="GENERATOR"),
            _make_evidence_item(evidence_type="TECHNOLOGY"),
            _make_evidence_item(evidence_type="CONTENT_HEADING"),
            _make_evidence_item(evidence_type="SOCIAL_PROFILE"),
            _make_evidence_item(evidence_type="COMPETITOR"),
        ]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert len(schema.seo) == 1
        assert len(schema.metadata) == 1
        assert len(schema.technology) == 1
        assert len(schema.content) == 1
        assert len(schema.social) == 1
        assert len(schema.competitors) == 1
        assert len(schema.evidence) == 6


class TestDiagnostics:
    def test_diagnostics_populated(self) -> None:
        items = [
            _make_evidence_item(evidence_type="SEO_TITLE"),
            _make_evidence_item(evidence_type="GENERATOR"),
        ]
        collection = _make_collection(items)
        schema = build_schema(collection)
        assert schema.diagnostics["total_evidence_items"] == 2
        assert schema.diagnostics["seo_items"] == 1
        assert schema.diagnostics["metadata_items"] == 1
        assert schema.diagnostics["technology_items"] == 0
        assert schema.diagnostics["build_timestamp"] is not None


class TestSerialization:
    def test_schema_is_frozen_dataclass(self) -> None:
        collection = _make_collection()
        schema = build_schema(collection)
        with pytest.raises(AttributeError):
            schema.site.url = "https://other.com"

    def test_sections_are_lists(self) -> None:
        collection = _make_collection()
        schema = build_schema(collection)
        assert isinstance(schema.seo, list)
        assert isinstance(schema.metadata, list)
        assert isinstance(schema.technology, list)
        assert isinstance(schema.content, list)
        assert isinstance(schema.social, list)
        assert isinstance(schema.competitors, list)
        assert isinstance(schema.evidence, list)


class TestSchemaValidation:
    def test_valid_schema_passes_validation(self) -> None:
        collection = _make_collection()
        schema = build_schema(collection)
        validate_schema(schema)

    def test_broken_schema_fails_validation(self) -> None:
        import jsonschema

        from aifme_scout.extractors.models import ScoutMeta, ScoutSchema, ScoutSite
        from aifme_scout.extractors.schema import validate as _validate

        broken = ScoutSchema(
            meta=ScoutMeta(schema_version="1.0.0", engine_version="1.0.0", timestamp=""),
            site=ScoutSite(url="", target_url=""),
            seo=[],
            metadata=[],
            technology=[],
            content=[],
            social=[],
            competitors=[],
            evidence=[],
            diagnostics={},
        )
        with pytest.raises(jsonschema.ValidationError):
            _validate(broken)

    def test_missing_required_field_fails_validation(self) -> None:
        import jsonschema

        from aifme_scout.extractors.models import ScoutMeta, ScoutSchema, ScoutSite
        from aifme_scout.extractors.schema import validate as _validate

        broken = ScoutSchema(
            meta=ScoutMeta(schema_version="1.0.0", engine_version="1.0.0", timestamp=""),
            site=ScoutSite(url="https://example.com", target_url="https://example.com"),
            seo=[],
            metadata=[],
            technology=[],
            content=[],
            social=[],
            competitors=[],
            evidence=[],
            diagnostics={"total_evidence_items": 0},
        )
        with pytest.raises(jsonschema.ValidationError):
            _validate(broken)


class TestGoldenOutput:
    def test_full_pipeline_output_validates_against_schema(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        technology_result = detect_technology(raw_site, parsed)
        content_result = extract_content(parsed)
        social_result = discover_social(parsed)
        competitor_result = resolve_competitors(parsed)
        evidence = collect_evidence(
            seo_result=seo_result,
            metadata_result=metadata_result,
            technology_result=technology_result,
            content_result=content_result,
            social_result=social_result,
            competitor_result=competitor_result,
            target_url="https://example.com",
        )
        schema = build_schema(evidence)
        validate_schema(schema)

    def test_golden_output_is_deterministic(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        evidence1 = collect_evidence(seo_result=seo_result, metadata_result=metadata_result)
        evidence2 = collect_evidence(seo_result=seo_result, metadata_result=metadata_result)
        schema1 = build_schema(evidence1)
        schema2 = build_schema(evidence2)
        assert (
            schema1.diagnostics["total_evidence_items"]
            == schema2.diagnostics["total_evidence_items"]
        )


class TestFullPipelineValidation:
    def test_wordpress_fixture_validates(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        technology_result = detect_technology(raw_site, parsed)
        content_result = extract_content(parsed)
        social_result = discover_social(parsed)
        competitor_result = resolve_competitors(parsed)
        evidence = collect_evidence(
            seo_result=seo_result,
            metadata_result=metadata_result,
            technology_result=technology_result,
            content_result=content_result,
            social_result=social_result,
            competitor_result=competitor_result,
            target_url="https://example.com",
        )
        schema = build_schema(evidence)
        assert schema.meta.schema_version == "1.0.0"
        assert schema.meta.engine_version == "1.0.0"
        assert schema.site.url == "https://example.com"
        assert schema.diagnostics["total_evidence_items"] > 0
        validate_schema(schema)
