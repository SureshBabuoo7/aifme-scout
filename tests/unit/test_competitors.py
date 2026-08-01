"""Unit tests for the Competitor Discovery module."""

from pathlib import Path

from aifme_scout.extractors import CompetitorResult, resolve_competitors
from aifme_scout.parser import parse
from aifme_scout.scanner.models import RawPage, RawSite


def _load_fixture(name: str) -> str:
    return Path("tests/fixtures/html").joinpath(name).read_text(encoding="utf-8")


def _make_raw_site(html: str, url: str = "https://example.com") -> RawSite:
    page = RawPage(
        url=url,
        final_url=url,
        status_code=200,
        headers={"content-type": "text/html"},
        html=html,
    )
    return RawSite(target_url=url, pages=[page], sitemap_urls=[])


def _parse(
    html: str,
    url: str = "https://example.com",
    user_supplied: list[str] | None = None,
) -> CompetitorResult:
    raw_site = _make_raw_site(html, url)
    parsed = parse(raw_site)
    return resolve_competitors(parsed, user_supplied=user_supplied)


def _get_competitors(result: CompetitorResult, url: str | None = None) -> list:
    if url is None:
        all_competitors = []
        for page in result.pages:
            all_competitors.extend(page.competitors)
        return all_competitors
    for page in result.pages:
        if page.url == url:
            return page.competitors
    return []


def _competitor_names(competitors: list) -> set[str]:
    return {c.name for c in competitors}


class TestUserSupplied:
    def test_user_supplied_competitors(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(
            html,
            user_supplied=["https://competitor1.com", "https://competitor2.com"],
        )
        names = _competitor_names(_get_competitors(result))
        assert "Competitor1" in names
        assert "Competitor2" in names

    def test_user_supplied_confidence_high(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(
            html,
            user_supplied=["https://competitor1.com"],
        )
        competitors = _get_competitors(result)
        assert len(competitors) == 1
        assert competitors[0].confidence == "high"
        assert competitors[0].discovery_method == "USER_SUPPLIED"

    def test_empty_user_supplied(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, user_supplied=[])
        assert _get_competitors(result) == []


class TestExplicitDiscovery:
    def test_comparison_page_detected(self) -> None:
        html = _load_fixture("comparison.html")
        result = _parse(html)
        names = _competitor_names(_get_competitors(result))
        assert "Competitor One" in names
        assert "Competitor Two" in names
        assert "Competitor Three" in names

    def test_alternatives_page_detected(self) -> None:
        html = _load_fixture("alternatives.html")
        result = _parse(html)
        names = _competitor_names(_get_competitors(result))
        assert "Alternative One" in names
        assert "Alternative Two" in names

    def test_explicit_confidence_high(self) -> None:
        html = _load_fixture("comparison.html")
        result = _parse(html)
        competitors = _get_competitors(result)
        assert len(competitors) > 0
        for competitor in competitors:
            assert competitor.confidence == "high"
            assert competitor.discovery_method == "EXPLICIT_DECLARATION"

    def test_no_competitors_on_regular_page(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert _get_competitors(result) == []


class TestDuplicateElimination:
    def test_duplicate_competitors_eliminated(self) -> None:
        raw_site = RawSite(
            target_url="https://example.com",
            pages=[
                RawPage(
                    url="https://example.com/",
                    final_url="https://example.com/",
                    status_code=200,
                    headers={"content-type": "text/html"},
                    html=_load_fixture("comparison.html"),
                ),
                RawPage(
                    url="https://example.com/about",
                    final_url="https://example.com/about",
                    status_code=200,
                    headers={"content-type": "text/html"},
                    html=_load_fixture("alternatives.html"),
                ),
            ],
            sitemap_urls=[],
        )
        parsed = parse(raw_site)
        result = resolve_competitors(parsed)
        all_competitors = _get_competitors(result)
        urls = [c.url for c in all_competitors]
        assert len(urls) == len(set(urls))


class TestProvenance:
    def test_provenance_preserved(self) -> None:
        html = _load_fixture("comparison.html")
        result = _parse(html)
        competitors = _get_competitors(result)
        assert len(competitors) > 0
        competitor = competitors[0]
        assert competitor.provenance is not None
        assert competitor.provenance.page_url == "https://example.com"
        assert competitor.provenance.tag == "a"
        assert competitor.provenance.attribute == "href"

    def test_evidence_preserved(self) -> None:
        html = _load_fixture("comparison.html")
        result = _parse(html)
        competitors = _get_competitors(result)
        assert len(competitors) > 0
        assert competitors[0].evidence is not None
        assert "comparison" in competitors[0].evidence.lower()


class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        html = _load_fixture("comparison.html")
        result1 = _parse(html)
        result2 = _parse(html)
        assert _competitor_names(_get_competitors(result1)) == _competitor_names(
            _get_competitors(result2)
        )


class TestDeferredHeuristic:
    def test_heuristic_status_deferred(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.heuristic_discovery_status == "DEFERRED"


class TestMissingCompetitors:
    def test_no_competitors_returns_empty(self) -> None:
        html = "<html><body></body></html>"
        result = _parse(html)
        assert _get_competitors(result) == []
