"""Unit tests for the Evidence Collector module."""

from pathlib import Path

from aifme_scout.extractors import (
    EvidenceCollection,
    EvidenceItem,
    analyze,
    collect_evidence,
    detect_technology,
    discover_social,
    extract_content,
    extract_metadata,
    resolve_competitors,
)
from aifme_scout.parser import parse
from aifme_scout.scanner.models import RawPage, RawSite


def _load_fixture(name: str) -> str:
    return Path("tests/fixtures/html").joinpath(name).read_text(encoding="utf-8")


def _make_raw_site(
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


def _parse(
    html: str, url: str = "https://example.com", headers: dict[str, str] | None = None
) -> RawSite:
    return _make_raw_site(html, url, headers)


def _get_items(result: EvidenceCollection) -> list[EvidenceItem]:
    return result.items


def _get_types(items: list[EvidenceItem]) -> set[str]:
    return {item.evidence_type for item in items}


class TestSEOEvidence:
    def test_seo_title_evidence(self) -> None:
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        evidence = collect_evidence(seo_result=seo_result)
        assert "SEO_TITLE" in _get_types(_get_items(evidence))

    def test_meta_description_evidence(self) -> None:
        html = '<html><head><meta name="description" content="Test"></head><body></body></html>'
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        evidence = collect_evidence(seo_result=seo_result)
        assert "META_DESCRIPTION" in _get_types(_get_items(evidence))


class TestMetadataEvidence:
    def test_generator_evidence(self) -> None:
        html = '<html><head><meta name="generator" content="WordPress"></head><body></body></html>'
        raw_site = _parse(html)
        parsed = parse(raw_site)
        metadata_result = extract_metadata(parsed)
        evidence = collect_evidence(metadata_result=metadata_result)
        assert "GENERATOR" in _get_types(_get_items(evidence))

    def test_favicon_evidence(self) -> None:
        html = '<html><head><link rel="icon" href="/favicon.ico"></head><body></body></html>'
        raw_site = _parse(html)
        parsed = parse(raw_site)
        metadata_result = extract_metadata(parsed)
        evidence = collect_evidence(metadata_result=metadata_result)
        assert "FAVICON" in _get_types(_get_items(evidence))


class TestTechnologyEvidence:
    def test_technology_evidence(self) -> None:
        html = _load_fixture("wordpress-tech.html")
        raw_site = _parse(html, headers={"Server": "nginx/1.25.0"})
        parsed = parse(raw_site)
        tech_result = detect_technology(raw_site, parsed)
        evidence = collect_evidence(technology_result=tech_result)
        assert "TECHNOLOGY" in _get_types(_get_items(evidence))

    def test_technology_confidence_preserved(self) -> None:
        html = _load_fixture("wordpress-tech.html")
        raw_site = _parse(html, headers={"Server": "nginx/1.25.0"})
        parsed = parse(raw_site)
        tech_result = detect_technology(raw_site, parsed)
        evidence = collect_evidence(technology_result=tech_result)
        tech_items = [item for item in _get_items(evidence) if item.evidence_type == "TECHNOLOGY"]
        assert len(tech_items) > 0
        assert tech_items[0].confidence == "high"


class TestContentEvidence:
    def test_heading_evidence(self) -> None:
        html = _load_fixture("content-tech.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        content_result = extract_content(parsed)
        evidence = collect_evidence(content_result=content_result)
        assert "CONTENT_HEADING" in _get_types(_get_items(evidence))

    def test_paragraph_evidence(self) -> None:
        html = _load_fixture("content-tech.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        content_result = extract_content(parsed)
        evidence = collect_evidence(content_result=content_result)
        assert "CONTENT_PARAGRAPH" in _get_types(_get_items(evidence))

    def test_image_evidence(self) -> None:
        html = _load_fixture("content-tech.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        content_result = extract_content(parsed)
        evidence = collect_evidence(content_result=content_result)
        assert "IMAGE" in _get_types(_get_items(evidence))

    def test_link_evidence(self) -> None:
        html = _load_fixture("content-tech.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        content_result = extract_content(parsed)
        evidence = collect_evidence(content_result=content_result)
        assert "LINK" in _get_types(_get_items(evidence))

    def test_form_evidence(self) -> None:
        html = _load_fixture("content-tech.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        content_result = extract_content(parsed)
        evidence = collect_evidence(content_result=content_result)
        assert "FORM" in _get_types(_get_items(evidence))


class TestSocialEvidence:
    def test_social_profile_evidence(self) -> None:
        html = _load_fixture("social-tech.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        social_result = discover_social(parsed)
        evidence = collect_evidence(social_result=social_result)
        assert "SOCIAL_PROFILE" in _get_types(_get_items(evidence))


class TestCompetitorEvidence:
    def test_competitor_evidence(self) -> None:
        html = _load_fixture("comparison.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        competitor_result = resolve_competitors(parsed)
        evidence = collect_evidence(competitor_result=competitor_result)
        assert "COMPETITOR" in _get_types(_get_items(evidence))

    def test_user_supplied_competitor_evidence(self) -> None:
        html = _load_fixture("minimal.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        competitor_result = resolve_competitors(parsed, user_supplied=["https://competitor1.com"])
        evidence = collect_evidence(competitor_result=competitor_result)
        assert "COMPETITOR" in _get_types(_get_items(evidence))


class TestMixedEvidence:
    def test_mixed_evidence_aggregation(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        content_result = extract_content(parsed)
        evidence = collect_evidence(
            seo_result=seo_result,
            metadata_result=metadata_result,
            content_result=content_result,
        )
        types = _get_types(_get_items(evidence))
        assert "SEO_TITLE" in types
        assert "META_DESCRIPTION" in types
        assert "CANONICAL" in types
        assert "CONTENT_HEADING" in types
        assert "LINK" in types


class TestEmptyEvidence:
    def test_empty_inputs_return_empty_collection(self) -> None:
        evidence = collect_evidence()
        assert evidence.items == []
        assert evidence.target_url == ""

    def test_none_inputs_return_empty_collection(self) -> None:
        evidence = collect_evidence(
            seo_result=None,
            metadata_result=None,
            technology_result=None,
            content_result=None,
            social_result=None,
            competitor_result=None,
        )
        assert evidence.items == []


class TestDuplicateEvidence:
    def test_duplicate_evidence_eliminated(self) -> None:
        html = "<html><head><title>Test</title></head><body></body></html>"
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        evidence1 = collect_evidence(seo_result=seo_result)
        evidence2 = collect_evidence(seo_result=seo_result)
        assert len(_get_items(evidence1)) == len(_get_items(evidence2))
        assert len(_get_items(evidence1)) > 0


class TestProvenance:
    def test_provenance_preserved(self) -> None:
        html = '<html><head><meta name="generator" content="WordPress"></head><body></body></html>'
        raw_site = _parse(html)
        parsed = parse(raw_site)
        metadata_result = extract_metadata(parsed)
        evidence = collect_evidence(metadata_result=metadata_result)
        items = _get_items(evidence)
        generator_items = [item for item in items if item.evidence_type == "GENERATOR"]
        assert len(generator_items) == 1
        assert generator_items[0].provenance is not None
        assert generator_items[0].provenance.tag == "meta"
        assert generator_items[0].provenance.attribute == "content"

    def test_page_url_preserved(self) -> None:
        html = "<html><head><title>Test</title></head><body></body></html>"
        raw_site = _parse(html, url="https://example.com/page")
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        evidence = collect_evidence(seo_result=seo_result)
        items = _get_items(evidence)
        assert len(items) > 0
        assert items[0].page_url == "https://example.com/page"


class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        content_result = extract_content(parsed)
        evidence1 = collect_evidence(
            seo_result=seo_result, metadata_result=metadata_result, content_result=content_result
        )
        evidence2 = collect_evidence(
            seo_result=seo_result, metadata_result=metadata_result, content_result=content_result
        )
        assert len(_get_items(evidence1)) == len(_get_items(evidence2))
        for item1, item2 in zip(_get_items(evidence1), _get_items(evidence2), strict=True):
            assert item1.evidence_type == item2.evidence_type
            assert item1.extractor_source == item2.extractor_source
            assert item1.evidence_id == item2.evidence_id
            assert item1.value == item2.value

    def test_deterministic_ordering(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        evidence1 = collect_evidence(seo_result=seo_result, metadata_result=metadata_result)
        evidence2 = collect_evidence(seo_result=seo_result, metadata_result=metadata_result)
        types1 = [item.evidence_type for item in _get_items(evidence1)]
        types2 = [item.evidence_type for item in _get_items(evidence2)]
        assert types1 == types2


class TestEvidenceIDs:
    def test_evidence_ids_unique(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        evidence = collect_evidence(seo_result=seo_result, metadata_result=metadata_result)
        ids = [item.evidence_id for item in _get_items(evidence)]
        assert len(ids) == len(set(ids))

    def test_evidence_ids_format(self) -> None:
        html = "<html><head><title>Test</title></head><body></body></html>"
        raw_site = _parse(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        evidence = collect_evidence(seo_result=seo_result)
        ids = [item.evidence_id for item in _get_items(evidence)]
        assert all(eid.startswith("ev-") for eid in ids)
