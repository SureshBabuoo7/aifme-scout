"""Integration tests for the Schema Builder module."""

from pathlib import Path

from aifme_scout.extractors import (
    build_schema,
    collect_evidence,
    extract_content,
    extract_metadata,
    validate_schema,
)
from aifme_scout.extractors.competitors import resolve as resolve_competitors
from aifme_scout.extractors.seo import analyze
from aifme_scout.extractors.social import discover as discover_social
from aifme_scout.extractors.technology import detect as detect_technology
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


class TestFullPipelineValidation:
    def test_wordpress_fixture_validates_against_schema(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _make_raw_site(html)
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
        assert schema.meta.schema_version == "1.0.0"
        assert schema.meta.engine_version == "1.0.0rc3"
        assert schema.site.url == "https://example.com"
        assert schema.diagnostics["total_evidence_items"] > 0

    def test_minimal_fixture_validates_against_schema(self) -> None:
        html = _load_fixture("minimal.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        content_result = extract_content(parsed)
        evidence = collect_evidence(
            seo_result=seo_result,
            metadata_result=metadata_result,
            content_result=content_result,
            target_url="https://example.com",
        )
        schema = build_schema(evidence)
        validate_schema(schema)

    def test_social_fixture_validates_against_schema(self) -> None:
        html = _load_fixture("social-tech.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        seo_result = analyze(parsed)
        metadata_result = extract_metadata(parsed)
        technology_result = detect_technology(raw_site, parsed)
        content_result = extract_content(parsed)
        social_result = discover_social(parsed)
        evidence = collect_evidence(
            seo_result=seo_result,
            metadata_result=metadata_result,
            technology_result=technology_result,
            content_result=content_result,
            social_result=social_result,
            target_url="https://example.com",
        )
        schema = build_schema(evidence)
        validate_schema(schema)
        assert schema.diagnostics["social_items"] > 0
