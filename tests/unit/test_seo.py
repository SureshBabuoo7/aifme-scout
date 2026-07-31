"""Unit tests for the SEO Extractor module."""

from pathlib import Path

from aifme_scout.extractors import SEOResult, analyze, to_simple_seo
from aifme_scout.parser import parse
from aifme_scout.scanner.models import RawPage, RawSite
from aifme_scout.utils.models import SEO


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


def _parse(html: str, url: str = "https://example.com") -> SEOResult:
    raw_site = _make_raw_site(html, url)
    parsed = parse(raw_site)
    return analyze(parsed)


class TestTitleExtraction:
    def test_title_extracted(self) -> None:
        html = _load_fixture("wordpress.html")
        result = _parse(html)
        assert result.pages[0].title is not None
        assert result.pages[0].title.value == "WordPress Site"

    def test_missing_title(self) -> None:
        html = "<html><head></head><body><p>No title</p></body></html>"
        result = _parse(html)
        assert result.pages[0].title is None


class TestMetaDescription:
    def test_meta_description_extracted(self) -> None:
        html = _load_fixture("wordpress.html")
        result = _parse(html)
        assert result.pages[0].meta_description is not None
        assert result.pages[0].meta_description.value == "A WordPress site"

    def test_missing_meta_description(self) -> None:
        html = "<html><head><title>Test</title></head><body><p>No description</p></body></html>"
        result = _parse(html)
        assert result.pages[0].meta_description is None


class TestCanonical:
    def test_canonical_extracted(self) -> None:
        html = _load_fixture("wordpress.html")
        result = _parse(html)
        assert result.pages[0].canonical is not None
        assert result.pages[0].canonical.value == "https://example.com/"

    def test_missing_canonical(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].canonical is None


class TestRobots:
    def test_robots_extracted(self) -> None:
        html = (
            '<html><head><meta name="robots" content="noindex, nofollow">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert result.pages[0].robots is not None
        assert result.pages[0].robots.value == "noindex, nofollow"
        assert result.pages[0].indexability.noindex is True
        assert result.pages[0].indexability.nofollow is True

    def test_missing_robots(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].robots is None


class TestHreflang:
    def test_hreflang_extracted(self) -> None:
        html = (
            "<html><head>"
            '<link rel="alternate" hreflang="en" href="https://example.com/en/">'
            '<link rel="alternate" hreflang="fr" href="https://example.com/fr/">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert result.pages[0].hreflang == ["en", "fr"]

    def test_missing_hreflang(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].hreflang == []


class TestCharset:
    def test_charset_extracted(self) -> None:
        html = '<html><head><meta charset="utf-8"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].charset == "utf-8"

    def test_missing_charset(self) -> None:
        html = "<html><head></head><body></body></html>"
        result = _parse(html)
        assert result.pages[0].charset is None


class TestViewport:
    def test_viewport_extracted(self) -> None:
        html = (
            '<html><head><meta name="viewport" content="width=device-width, initial-scale=1">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert result.pages[0].viewport == "width=device-width, initial-scale=1"

    def test_missing_viewport(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].viewport is None


class TestLanguage:
    def test_language_from_html_lang(self) -> None:
        html = '<html lang="en"><head></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].language == "en"

    def test_missing_language(self) -> None:
        html = "<html><head></head><body></body></html>"
        result = _parse(html)
        assert result.pages[0].language is None


class TestHeadingHierarchy:
    def test_h1_detected(self) -> None:
        html = _load_fixture("wordpress.html")
        result = _parse(html)
        assert result.pages[0].heading_hierarchy.has_h1 is True
        assert any(h.level == 1 for h in result.pages[0].heading_hierarchy.headings)

    def test_duplicate_h1_detected(self) -> None:
        html = "<html><body><h1>A</h1><h1>A</h1></body></html>"
        result = _parse(html)
        assert result.pages[0].heading_hierarchy.duplicate_h1_count == 1
        assert result.pages[0].heading_hierarchy.valid is False

    def test_no_headings(self) -> None:
        html = "<html><body><p>No headings</p></body></html>"
        result = _parse(html)
        assert result.pages[0].heading_hierarchy.has_h1 is False
        assert result.pages[0].heading_hierarchy.valid is False


class TestOpenGraph:
    def test_open_graph_extracted(self) -> None:
        html = _load_fixture("wordpress.html")
        result = _parse(html)
        assert result.pages[0].open_graph.title == "WordPress Site"
        assert result.pages[0].open_graph.description == "A WordPress site"

    def test_missing_open_graph(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].open_graph.title is None
        assert result.pages[0].open_graph.description is None


class TestTwitterCard:
    def test_twitter_card_extracted(self) -> None:
        html = (
            "<html><head>"
            '<meta name="twitter:title" content="Twitter Title">'
            '<meta name="twitter:description" content="Twitter Desc">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert result.pages[0].twitter_card.title == "Twitter Title"
        assert result.pages[0].twitter_card.description == "Twitter Desc"

    def test_missing_twitter_card(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].twitter_card.title is None
        assert result.pages[0].twitter_card.description is None


class TestStructuredData:
    def test_json_ld_detected(self) -> None:
        html = (
            "<html><head>"
            '<script type="application/ld+json">{"@context":"https://schema.org"}</script>'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert result.pages[0].structured_data.has_json_ld is True
        assert result.pages[0].structured_data.count == 1

    def test_no_structured_data(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].structured_data.count == 0


class TestIndexability:
    def test_noindex_detected(self) -> None:
        html = '<html><head><meta name="robots" content="noindex"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].indexability.noindex is True

    def test_nofollow_detected(self) -> None:
        html = '<html><head><meta name="robots" content="nofollow"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].indexability.nofollow is True

    def test_noarchive_detected(self) -> None:
        html = '<html><head><meta name="robots" content="noarchive"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].indexability.noarchive is True

    def test_nosnippet_detected(self) -> None:
        html = '<html><head><meta name="robots" content="nosnippet"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].indexability.nosnippet is True


class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        html = _load_fixture("wordpress.html")
        result1 = _parse(html)
        result2 = _parse(html)
        assert result1.pages[0].title == result2.pages[0].title
        assert result1.pages[0].meta_description == result2.pages[0].meta_description
        assert (
            result1.pages[0].heading_hierarchy.headings
            == result2.pages[0].heading_hierarchy.headings
        )


class TestToSimpleSEO:
    def test_conversion(self) -> None:
        html = _load_fixture("wordpress.html")
        result = _parse(html)
        simple = to_simple_seo(result)
        assert isinstance(simple, SEO)
        assert simple.has_title is True
        assert simple.has_meta_description is True
        assert simple.has_canonical is True
        assert simple.heading_structure_valid is True

    def test_empty_result(self) -> None:
        result = SEOResult(target_url="https://example.com")
        simple = to_simple_seo(result)
        assert simple.has_title is False
        assert simple.has_meta_description is False
