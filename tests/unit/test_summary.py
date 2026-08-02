"""Unit tests for the Summary Builder module."""



from aifme_scout.engine.summary import _classify_target, summarize
from aifme_scout.extractors.models import (
    EvidenceItem,
    EvidenceProvenance,
    ScoutMeta,
    ScoutSchema,
    ScoutSite,
)
from aifme_scout.utils.constants import ScanMode
from aifme_scout.utils.models import Summary


def _make_evidence(
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


def _make_schema(
    evidence_items: list[EvidenceItem] | None = None,
    target_url: str = "https://example.com",
) -> ScoutSchema:
    if evidence_items is None:
        evidence_items = [_make_evidence()]
    return ScoutSchema(
        meta=ScoutMeta(
            schema_version="1.0.0",
            engine_version="1.0.0-rc1",
            timestamp="2024-01-01T00:00:00+00:00",
        ),
        site=ScoutSite(url=target_url, target_url=target_url),
        seo=[item for item in evidence_items if item.evidence_type == "SEO_TITLE"],
        metadata=[item for item in evidence_items if item.evidence_type == "GENERATOR"],
        technology=[item for item in evidence_items if item.evidence_type == "TECHNOLOGY"],
        content=[item for item in evidence_items if item.evidence_type == "CONTENT_HEADING"],
        social=[item for item in evidence_items if item.evidence_type == "SOCIAL_PROFILE"],
        competitors=[item for item in evidence_items if item.evidence_type == "COMPETITOR"],
        evidence=evidence_items,
        diagnostics={
            "total_evidence_items": len(evidence_items),
            "seo_items": sum(1 for i in evidence_items if i.evidence_type == "SEO_TITLE"),
            "metadata_items": sum(1 for i in evidence_items if i.evidence_type == "GENERATOR"),
            "technology_items": sum(1 for i in evidence_items if i.evidence_type == "TECHNOLOGY"),
            "content_items": sum(1 for i in evidence_items if i.evidence_type == "CONTENT_HEADING"),
            "social_items": sum(1 for i in evidence_items if i.evidence_type == "SOCIAL_PROFILE"),
            "competitor_items": sum(1 for i in evidence_items if i.evidence_type == "COMPETITOR"),
            "build_timestamp": "2024-01-01T00:00:00+00:00",
        },
    )


class TestEmptySchema:
    def test_empty_schema_returns_summary(self) -> None:
        schema = _make_schema([])
        result = summarize(schema)
        assert isinstance(result, Summary)
        assert result.text != ""
        assert schema.site.url in result.evidence_refs

    def test_empty_schema_all_sections_present(self) -> None:
        schema = _make_schema([])
        result = summarize(schema)
        assert "## Executive Summary" in result.text
        assert "## Website Overview" in result.text
        assert "## SEO Summary" in result.text
        assert "## Metadata Summary" in result.text
        assert "## Technology Summary" in result.text
        assert "## Content Summary" in result.text
        assert "## Social Presence Summary" in result.text
        assert "## Competitor Summary" in result.text
        assert "## Diagnostics" in result.text
        assert "## Data Completeness" in result.text


class TestCompleteSchema:
    def test_complete_schema_returns_summary(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
            _make_evidence(evidence_id="ev-000002", evidence_type="GENERATOR"),
            _make_evidence(
                evidence_id="ev-000003",
                evidence_type="TECHNOLOGY",
                value={"name": "React", "category": "frontend", "confidence": "high"},
            ),
            _make_evidence(evidence_id="ev-000004", evidence_type="CONTENT_HEADING"),
            _make_evidence(evidence_id="ev-000005", evidence_type="SOCIAL_PROFILE"),
            _make_evidence(evidence_id="ev-000006", evidence_type="COMPETITOR"),
        ]
        schema = _make_schema(items)
        result = summarize(schema)
        assert isinstance(result, Summary)
        assert result.text != ""
        assert len(result.evidence_refs) > 0

    def test_complete_schema_all_sections_present(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
            _make_evidence(evidence_id="ev-000002", evidence_type="GENERATOR"),
        ]
        schema = _make_schema(items)
        result = summarize(schema)
        assert "## Executive Summary" in result.text
        assert "## Website Overview" in result.text
        assert "## SEO Summary" in result.text
        assert "## Metadata Summary" in result.text
        assert "## Technology Summary" in result.text
        assert "## Content Summary" in result.text
        assert "## Social Presence Summary" in result.text
        assert "## Competitor Summary" in result.text
        assert "## Diagnostics" in result.text
        assert "## Data Completeness" in result.text


class TestPartialSchema:
    def test_partial_schema_no_technology(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
        ]
        schema = _make_schema(items)
        result = summarize(schema)
        assert "## Technology Summary" in result.text
        assert "Technology: 0 items (missing)" in result.text

    def test_partial_schema_no_social(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
        ]
        schema = _make_schema(items)
        result = summarize(schema)
        assert "## Social Presence Summary" in result.text


class TestStableOrdering:
    def test_same_input_same_output(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
            _make_evidence(evidence_id="ev-000002", evidence_type="GENERATOR"),
        ]
        schema = _make_schema(items)
        result1 = summarize(schema)
        result2 = summarize(schema)
        assert result1.text == result2.text
        assert result1.evidence_refs == result2.evidence_refs

    def test_deterministic_ordering_of_refs(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000002", evidence_type="GENERATOR"),
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
        ]
        schema = _make_schema(items)
        result1 = summarize(schema)
        result2 = summarize(schema)
        assert result1.evidence_refs == result2.evidence_refs


class TestEvidenceTraceability:
    def test_evidence_refs_populated(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
            _make_evidence(evidence_id="ev-000002", evidence_type="GENERATOR"),
        ]
        schema = _make_schema(items)
        result = summarize(schema)
        assert "ev-000001" in result.evidence_refs
        assert "ev-000002" in result.evidence_refs

    def test_no_orphan_refs(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE"),
        ]
        schema = _make_schema(items)
        result = summarize(schema)
        valid_refs = [item.evidence_id for item in schema.evidence] + [schema.site.url]
        for ref in result.evidence_refs:
            assert ref in valid_refs

    def test_target_url_preserved(self) -> None:
        schema = _make_schema(target_url="https://test.example.com")
        result = summarize(schema)
        assert "https://test.example.com" in result.text


class TestNoInventedFacts:
    def test_no_invented_facts_empty_schema(self) -> None:
        schema = _make_schema([])
        result = summarize(schema)
        assert "Target site:" in result.text
        assert "Evidence items collected: 0" in result.text

    def test_no_invented_facts_partial_schema(self) -> None:
        items = [
            _make_evidence(evidence_id="ev-000001", evidence_type="SEO_TITLE", value="Test Title"),
        ]
        schema = _make_schema(items)
        result = summarize(schema)
        assert "Test Title" in result.text
        assert "ev-000001" in result.evidence_refs


class TestSerialization:
    def test_summary_is_dataclass(self) -> None:
        schema = _make_schema([])
        result = summarize(schema)
        assert isinstance(result, Summary)

    def test_summary_fields(self) -> None:
        schema = _make_schema([])
        result = summarize(schema)
        assert isinstance(result.text, str)
        assert isinstance(result.evidence_refs, list)


class TestModeFlag:
    def test_no_llm_mode_produces_summary(self) -> None:
        schema = _make_schema([])
        result = summarize(schema, mode=ScanMode.NO_LLM)
        assert isinstance(result, Summary)
        assert result.text != ""

    def test_llm_mode_falls_back_to_template(self) -> None:
        schema = _make_schema([])
        result = summarize(schema, mode=ScanMode.LLM)
        assert isinstance(result, Summary)
        assert result.text != ""


class TestTargetClassification:
    def test_general_classification_for_empty_schema(self) -> None:
        schema = _make_schema([])
        classification, _ = _classify_target(schema)
        assert classification == "general"

    def test_ecommerce_classification(self) -> None:
        items = [
            _make_evidence(
                evidence_id="ev-000001",
                evidence_type="TECHNOLOGY",
                value={"name": "Shopify", "category": "e-commerce", "confidence": "high"},
            ),
        ]
        schema = _make_schema(items)
        classification, _ = _classify_target(schema)
        assert classification == "e-commerce"

    def test_saas_classification(self) -> None:
        items = [
            _make_evidence(
                evidence_id="ev-000001",
                evidence_type="TECHNOLOGY",
                value={"name": "React", "category": "frontend", "confidence": "high"},
            ),
            _make_evidence(
                evidence_id="ev-000002",
                evidence_type="CONTENT_HEADING",
                value="Our SaaS platform offers API access",
            ),
        ]
        schema = _make_schema(items, target_url="https://saas.example.com")
        classification, _ = _classify_target(schema)
        assert classification == "saas"
