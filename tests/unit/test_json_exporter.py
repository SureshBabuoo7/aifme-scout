"""Unit tests for the JSON Exporter module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aifme_scout.exporters.json_exporter import export, export_to_file
from aifme_scout.extractors.models import (
    EvidenceItem,
    EvidenceProvenance,
    ScoutMeta,
    ScoutSchema,
    ScoutSite,
)


def _make_evidence_item(
    evidence_id: str = "ev-000001",
    evidence_type: str = "SEO_TITLE",
    extractor_source: str = "seo",
    value: object = "Test Title",
    page_url: str = "https://example.com",
    confidence: str = "high",
) -> EvidenceItem:
    """Create a minimal EvidenceItem for testing."""
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


def _make_schema(
    evidence_items: list[EvidenceItem] | None = None,
    target_url: str = "https://example.com",
) -> ScoutSchema:
    """Create a minimal ScoutSchema for testing."""
    if evidence_items is None:
        evidence_items = [_make_evidence_item()]
    return ScoutSchema(
        meta=ScoutMeta(
            schema_version="1.0.0",
            engine_version="1.0.0-rc2",
            timestamp="2024-01-01T00:00:00+00:00",
        ),
        site=ScoutSite(url=target_url, target_url=target_url),
        seo=[item for item in evidence_items if item.evidence_type == "SEO_TITLE"],
        metadata=[
            item for item in evidence_items if item.evidence_type == "GENERATOR"
        ],
        technology=[
            item for item in evidence_items if item.evidence_type == "TECHNOLOGY"
        ],
        content=[
            item
            for item in evidence_items
            if item.evidence_type == "CONTENT_HEADING"
        ],
        social=[
            item for item in evidence_items if item.evidence_type == "SOCIAL_PROFILE"
        ],
        competitors=[
            item for item in evidence_items if item.evidence_type == "COMPETITOR"
        ],
        evidence=evidence_items,
        diagnostics={
            "total_evidence_items": len(evidence_items),
            "seo_items": sum(
                1 for i in evidence_items if i.evidence_type == "SEO_TITLE"
            ),
            "metadata_items": sum(
                1 for i in evidence_items if i.evidence_type == "GENERATOR"
            ),
            "technology_items": sum(
                1 for i in evidence_items if i.evidence_type == "TECHNOLOGY"
            ),
            "content_items": sum(
                1 for i in evidence_items if i.evidence_type == "CONTENT_HEADING"
            ),
            "social_items": sum(
                1 for i in evidence_items if i.evidence_type == "SOCIAL_PROFILE"
            ),
            "competitor_items": sum(
                1 for i in evidence_items if i.evidence_type == "COMPETITOR"
            ),
            "build_timestamp": "2024-01-01T00:00:00+00:00",
        },
    )


class TestEmptySchema:
    """Tests for exporting an empty ScoutSchema."""

    def test_empty_schema_exports_valid_json(self) -> None:
        schema = _make_schema([])
        result = export(schema)
        assert isinstance(result, str)
        data = json.loads(result)
        assert data["meta"]["schema_version"] == "1.0.0"
        assert data["site"]["url"] == "https://example.com"
        assert data["seo"] == []
        assert data["metadata"] == []
        assert data["technology"] == []
        assert data["content"] == []
        assert data["social"] == []
        assert data["competitors"] == []
        assert data["evidence"] == []
        assert data["diagnostics"]["total_evidence_items"] == 0

    def test_empty_schema_round_trip(self) -> None:
        schema = _make_schema([])
        result = export(schema)
        data = json.loads(result)
        assert data["evidence"] == []
        assert data["diagnostics"]["build_timestamp"] == "2024-01-01T00:00:00+00:00"


class TestCompleteSchema:
    """Tests for exporting a complete ScoutSchema with evidence items."""

    def test_complete_schema_exports_valid_json(self) -> None:
        items = [
            _make_evidence_item(
                evidence_id="ev-000001",
                evidence_type="SEO_TITLE",
                value="Test Title",
            ),
            _make_evidence_item(
                evidence_id="ev-000002",
                evidence_type="GENERATOR",
                value="WordPress",
            ),
            _make_evidence_item(
                evidence_id="ev-000003",
                evidence_type="TECHNOLOGY",
                value={"name": "React", "category": "frontend", "confidence": "high"},
            ),
            _make_evidence_item(
                evidence_id="ev-000004",
                evidence_type="CONTENT_HEADING",
                value={"level": 1, "text": "Hello"},
            ),
            _make_evidence_item(
                evidence_id="ev-000005",
                evidence_type="SOCIAL_PROFILE",
                value={"platform": "twitter", "url": "https://twitter.com/test"},
            ),
            _make_evidence_item(
                evidence_id="ev-000006",
                evidence_type="COMPETITOR",
                value={"name": "Competitor", "url": "https://competitor.com"},
            ),
        ]
        schema = _make_schema(items)
        result = export(schema)
        data = json.loads(result)
        assert len(data["seo"]) == 1
        assert len(data["metadata"]) == 1
        assert len(data["technology"]) == 1
        assert len(data["content"]) == 1
        assert len(data["social"]) == 1
        assert len(data["competitors"]) == 1
        assert len(data["evidence"]) == 6
        assert data["diagnostics"]["total_evidence_items"] == 6

    def test_complete_schema_preserves_evidence_ids(self) -> None:
        items = [
            _make_evidence_item(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
            _make_evidence_item(evidence_id="ev-000002", evidence_type="GENERATOR"),
        ]
        schema = _make_schema(items)
        result = export(schema)
        data = json.loads(result)
        evidence_ids = [item["evidence_id"] for item in data["evidence"]]
        assert "ev-000001" in evidence_ids
        assert "ev-000002" in evidence_ids


class TestStableOutput:
    """Tests for stable, deterministic output."""

    def test_same_input_same_output(self) -> None:
        schema = _make_schema([_make_evidence_item()])
        result1 = export(schema)
        result2 = export(schema)
        assert result1 == result2

    def test_output_is_pretty_printed(self) -> None:
        schema = _make_schema([_make_evidence_item()])
        result = export(schema)
        assert "\n" in result
        assert "  " in result

    def test_output_keys_are_sorted(self) -> None:
        schema = _make_schema([_make_evidence_item()])
        result = export(schema)
        data = json.loads(result)
        assert list(data.keys()) == sorted(data.keys())


class TestFileExport:
    """Tests for export_to_file."""

    def test_file_export_writes_utf8(self, tmp_path: Path) -> None:
        schema = _make_schema([_make_evidence_item()])
        file_path = tmp_path / "scan-result.json"
        export_to_file(schema, file_path)
        content = file_path.read_text(encoding="utf-8")
        assert content == export(schema)

    def test_file_export_creates_file(self, tmp_path: Path) -> None:
        schema = _make_schema([_make_evidence_item()])
        file_path = tmp_path / "scan-result.json"
        assert not file_path.exists()
        export_to_file(schema, file_path)
        assert file_path.exists()

    def test_file_export_invalid_path_raises(self) -> None:
        schema = _make_schema([])
        with pytest.raises(OSError):
            export_to_file(schema, "/invalid/path/that/does/not/exist/output.json")


class TestUTF8Encoding:
    """Tests for UTF-8 encoding support."""

    def test_utf8_characters_preserved(self, tmp_path: Path) -> None:
        items = [
            _make_evidence_item(
                evidence_id="ev-000001",
                evidence_type="SEO_TITLE",
                value="Café résumé naïve 日本語",
            )
        ]
        schema = _make_schema(items)
        file_path = tmp_path / "utf8.json"
        export_to_file(schema, file_path)
        content = file_path.read_text(encoding="utf-8")
        assert "Café résumé naïve 日本語" in content
        content.encode("utf-8").decode("utf-8")

    def test_export_returns_utf8_string(self) -> None:
        items = [
            _make_evidence_item(
                evidence_id="ev-000001",
                evidence_type="SEO_TITLE",
                value="Café résumé naïve 日本語",
            )
        ]
        schema = _make_schema(items)
        result = export(schema)
        assert isinstance(result, str)
        result.encode("utf-8").decode("utf-8")


class TestSchemaValidation:
    """Tests for JSON Schema compliance."""

    def test_export_validates_against_schema(self) -> None:
        import jsonschema

        schema = _make_schema([_make_evidence_item()])
        result = export(schema)
        data = json.loads(result)
        schema_dict = json.loads(
            Path("schemas/v1/scan-result.schema.json").read_text(encoding="utf-8")
        )
        jsonschema.validate(instance=data, schema=schema_dict)

    def test_empty_schema_validates_against_schema(self) -> None:
        import jsonschema

        schema = _make_schema([])
        result = export(schema)
        data = json.loads(result)
        schema_dict = json.loads(
            Path("schemas/v1/scan-result.schema.json").read_text(encoding="utf-8")
        )
        jsonschema.validate(instance=data, schema=schema_dict)


class TestRoundTripSerialization:
    """Tests for round-trip serialization."""

    def test_round_trip_preserves_meta(self) -> None:
        schema = _make_schema([_make_evidence_item()])
        result = export(schema)
        data = json.loads(result)
        assert data["meta"]["schema_version"] == "1.0.0"
        assert data["meta"]["engine_version"] == "1.0.0-rc2"
        assert data["meta"]["timestamp"] == "2024-01-01T00:00:00+00:00"

    def test_round_trip_preserves_site(self) -> None:
        schema = _make_schema([_make_evidence_item()], target_url="https://test.example.com")
        result = export(schema)
        data = json.loads(result)
        assert data["site"]["url"] == "https://test.example.com"
        assert data["site"]["target_url"] == "https://test.example.com"

    def test_round_trip_preserves_evidence(self) -> None:
        items = [
            _make_evidence_item(
                evidence_id="ev-000001",
                evidence_type="SEO_TITLE",
                value="Test Title",
                confidence="high",
            )
        ]
        schema = _make_schema(items)
        result = export(schema)
        data = json.loads(result)
        assert data["evidence"][0]["evidence_id"] == "ev-000001"
        assert data["evidence"][0]["value"] == "Test Title"
        assert data["evidence"][0]["confidence"] == "high"

    def test_round_trip_preserves_diagnostics(self) -> None:
        schema = _make_schema([_make_evidence_item()])
        result = export(schema)
        data = json.loads(result)
        assert data["diagnostics"]["total_evidence_items"] == 1
        assert data["diagnostics"]["seo_items"] == 1
        assert data["diagnostics"]["build_timestamp"] == "2024-01-01T00:00:00+00:00"


class TestDeterministicOrdering:
    """Tests for deterministic output ordering."""

    def test_deterministic_output_across_runs(self) -> None:
        items = [
            _make_evidence_item(evidence_id="ev-000002", evidence_type="GENERATOR"),
            _make_evidence_item(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
            _make_evidence_item(
                evidence_id="ev-000003",
                evidence_type="TECHNOLOGY",
                value={"name": "React", "category": "frontend"},
            ),
        ]
        schema = _make_schema(items)
        result1 = export(schema)
        result2 = export(schema)
        assert result1 == result2

    def test_nested_dict_keys_are_sorted(self) -> None:
        items = [
            _make_evidence_item(
                evidence_id="ev-000001",
                evidence_type="TECHNOLOGY",
                value={"z_key": 1, "a_key": 2},
            )
        ]
        schema = _make_schema(items)
        result = export(schema)
        data = json.loads(result)
        value_keys = list(data["evidence"][0]["value"].keys())
        assert value_keys == sorted(value_keys)


class TestErrorHandling:
    """Tests for error handling."""

    def test_serialization_error_handling(self) -> None:
        class UnserializableStr:
            def __str__(self) -> str:
                raise TypeError("Cannot serialize")

        item = _make_evidence_item(value=UnserializableStr())
        schema = _make_schema([item])
        with pytest.raises(TypeError):
            export(schema)

    def test_never_mutates_input_schema(self) -> None:
        schema = _make_schema([_make_evidence_item()])
        original_evidence_count = len(schema.evidence)
        export(schema)
        assert len(schema.evidence) == original_evidence_count
        assert schema.evidence[0].evidence_id == "ev-000001"
