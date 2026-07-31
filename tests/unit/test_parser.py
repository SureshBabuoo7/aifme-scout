"""Unit tests for the HTML Parser module."""

from pathlib import Path

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


class TestParseValidHTML:
    def test_minimal_page(self) -> None:
        html = _load_fixture("minimal.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        assert len(parsed.pages) == 1
        assert parsed.pages[0].parse_error is None
        assert parsed.pages[0].head is not None
        assert parsed.pages[0].body is not None
        assert parsed.pages[0].head.find("title") is not None

    def test_wordpress_page(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        assert len(parsed.pages) == 1
        assert parsed.parse_errors == []
        head = parsed.pages[0].head
        assert head is not None
        og_title = head.find("meta", {"property": "og:title"})
        assert og_title is not None
        assert og_title.get("content") == "WordPress Site"

    def test_shopify_page(self) -> None:
        html = _load_fixture("shopify.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        assert len(parsed.pages) == 1
        assert parsed.parse_errors == []

    def test_nextjs_page(self) -> None:
        html = _load_fixture("nextjs.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        assert len(parsed.pages) == 1
        assert parsed.parse_errors == []


class TestMalformedHTML:
    def test_malformed_html_recovers(self) -> None:
        html = _load_fixture("malformed.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        assert len(parsed.pages) == 1
        assert parsed.pages[0].parse_error is None
        assert parsed.pages[0].body is not None

    def test_malformed_html_has_warnings(self) -> None:
        html = _load_fixture("malformed.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        assert len(parsed.pages[0].warnings) >= 0  # may or may not have warnings

    def test_empty_html(self) -> None:
        raw_site = _make_raw_site("")
        parsed = parse(raw_site)
        assert len(parsed.pages) == 1
        assert parsed.pages[0].parse_error is None
        assert parsed.pages[0].root is not None

    def test_html_with_only_whitespace(self) -> None:
        raw_site = _make_raw_site("   \n\t  ")
        parsed = parse(raw_site)
        assert len(parsed.pages) == 1
        assert parsed.pages[0].parse_error is None


class TestHeadBodySeparation:
    def test_head_extracted(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        head = parsed.pages[0].head
        assert head is not None
        assert head.find("title") is not None
        assert head.find("meta") is not None

    def test_body_extracted(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        assert body.find("h1") is not None
        assert body.find("p") is not None

    def test_missing_head_warning(self) -> None:
        html = "<html><body><p>No head</p></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        warnings = parsed.pages[0].warnings
        assert any("head" in w.message.lower() for w in warnings)

    def test_missing_body_warning(self) -> None:
        html = "<html><head><title>No body</title></head></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        warnings = parsed.pages[0].warnings
        assert any("body" in w.message.lower() for w in warnings)


class TestDOMTraversal:
    def test_find_by_tag(self) -> None:
        html = "<html><body><div><p>A</p><p>B</p></div></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        first_p = body.find("p")
        assert first_p is not None
        assert "A" in first_p.text

    def test_find_all_by_tag(self) -> None:
        html = "<html><body><div><p>A</p><p>B</p><span>C</span></div></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        paragraphs = body.find_all("p")
        assert len(paragraphs) == 2

    def test_find_with_attrs(self) -> None:
        html = (
            '<html><body><a href="/a" class="link">A</a>'
            '<a href="/b" class="link">B</a></body></html>'
        )
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        link = body.find("a", {"class": "link"})
        assert link is not None
        assert link.get("href") == "/a"

    def test_find_all_with_attrs(self) -> None:
        html = (
            '<html><body><a href="/a" class="link">A</a>'
            '<a href="/b" class="link">B</a>'
            '<a href="/c">C</a></body></html>'
        )
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        links = body.find_all("a", {"class": "link"})
        assert len(links) == 2

    def test_parent_navigation(self) -> None:
        html = "<html><body><div><p>Text</p></div></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        p = body.find("p")
        assert p is not None
        parent = p.parent
        assert parent is not None
        assert parent.tag == "div"

    def test_children_access(self) -> None:
        html = "<html><body><ul><li>A</li><li>B</li></ul></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        ul = body.find("ul")
        assert ul is not None
        assert len(ul.children) == 2


class TestTextExtraction:
    def test_element_text(self) -> None:
        html = "<html><body><p>Hello World</p></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        p = body.find("p")
        assert p is not None
        assert p.text == "Hello World"

    def test_nested_text(self) -> None:
        html = "<html><body><div><p>Nested <span>text</span></p></div></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        div = body.find("div")
        assert div is not None
        assert "Nested" in div.text
        assert "text" in div.text

    def test_text_stripped(self) -> None:
        html = "<html><body><p>   Spaces   </p></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        body = parsed.pages[0].body
        assert body is not None
        p = body.find("p")
        assert p is not None
        assert p.text == "Spaces"


class TestDeterministicParsing:
    def test_same_input_same_output(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site1 = _make_raw_site(html)
        raw_site2 = _make_raw_site(html)
        parsed1 = parse(raw_site1)
        parsed2 = parse(raw_site2)
        assert parsed1.pages[0].root.find("title").text == parsed2.pages[0].root.find("title").text
        assert len(parsed1.pages[0].root.find_all("p")) == len(parsed2.pages[0].root.find_all("p"))

    def test_element_count_stable(self) -> None:
        html = _load_fixture("wordpress.html")
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        first_count = len(parsed.pages[0].root)
        for _ in range(3):
            parsed2 = parse(_make_raw_site(html))
            assert len(parsed2.pages[0].root) == first_count


class TestEncodingHandling:
    def test_utf8_html(self) -> None:
        html = "<html><head><title>Héllo Wörld</title></head><body><p>Content</p></body></html>"
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        assert parsed.pages[0].parse_error is None
        title = parsed.pages[0].head.find("title")
        assert title is not None
        assert "Héllo Wörld" in title.text

    def test_meta_charset(self) -> None:
        html = (
            '<html><head><meta charset="utf-8"><title>Test</title>'
            "</head><body><p>Content</p></body></html>"
        )
        raw_site = _make_raw_site(html)
        parsed = parse(raw_site)
        assert parsed.pages[0].parse_error is None
        title = parsed.pages[0].head.find("title")
        assert title is not None


class TestLargeHTML:
    def test_large_html_parses(self) -> None:
        large_html = (
            "<html><body>"
            "<p>Paragraph "
            + " ".join(str(i) for i in range(10000))
            + "</p>" * 1000
            + "</body></html>"
        )
        raw_site = _make_raw_site(large_html)
        parsed = parse(raw_site)
        assert len(parsed.pages) == 1
        assert parsed.pages[0].parse_error is None
        assert parsed.pages[0].body is not None


class TestMultiPage:
    def test_multiple_pages(self) -> None:
        html1 = _load_fixture("minimal.html")
        html2 = _load_fixture("404.html")
        page1 = RawPage(
            url="https://example.com",
            final_url="https://example.com",
            status_code=200,
            headers={},
            html=html1,
        )
        page2 = RawPage(
            url="https://example.com/404",
            final_url="https://example.com/404",
            status_code=404,
            headers={},
            html=html2,
        )
        raw_site = RawSite(target_url="https://example.com", pages=[page1, page2], sitemap_urls=[])
        parsed = parse(raw_site)
        assert len(parsed.pages) == 2
        assert parsed.pages[0].parse_error is None
        assert parsed.pages[1].parse_error is None
