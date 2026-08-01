"""Unit tests for the Content Extractor module."""

from pathlib import Path

from aifme_scout.extractors import ContentResult, extract_content
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


def _parse(html: str, url: str = "https://example.com") -> ContentResult:
    raw_site = _make_raw_site(html, url)
    parsed = parse(raw_site)
    return extract_content(parsed)


class TestHeadings:
    def test_headings_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        headings = result.pages[0].headings
        assert len(headings) == 3
        assert headings[0].level == 1
        assert headings[0].text == "Welcome to Our Store"
        assert headings[1].level == 2
        assert headings[1].text == "Products"
        assert headings[2].level == 3
        assert headings[2].text == "Featured"

    def test_no_headings(self) -> None:
        html = "<html><body><p>No headings here.</p></body></html>"
        result = _parse(html)
        assert result.pages[0].headings == []


class TestParagraphs:
    def test_paragraphs_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        paragraphs = result.pages[0].paragraphs
        assert len(paragraphs) == 2
        assert paragraphs[0].text == "This is the best store ever."
        assert paragraphs[1].text == "© 2024 My Store"

    def test_no_paragraphs(self) -> None:
        html = "<html><body></body></html>"
        result = _parse(html)
        assert result.pages[0].paragraphs == []


class TestLists:
    def test_lists_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        lists = result.pages[0].lists
        assert len(lists) == 2
        ul = next(item for item in lists if item.list_type == "ul")
        assert len(ul.items) == 3
        assert ul.items[0].text == "Product A"
        assert ul.items[1].text == "Product B"
        assert ul.items[2].text == "Product C"
        ol = next(item for item in lists if item.list_type == "ol")
        assert len(ol.items) == 3
        assert ol.items[0].text == "Home"
        assert ol.items[1].text == "Products"
        assert ol.items[2].text == "Product Details"

    def test_no_lists(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].lists == []


class TestTables:
    def test_tables_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        tables = result.pages[0].tables
        assert len(tables) == 1
        assert tables[0].headers == ["Name", "Price"]
        assert len(tables[0].rows) == 2
        assert tables[0].rows[0] == ["Product A", "$10"]
        assert tables[0].rows[1] == ["Product B", "$20"]

    def test_no_tables(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].tables == []


class TestImages:
    def test_images_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        images = result.pages[0].images
        assert len(images) == 1
        assert images[0].src == "/images/product.jpg"
        assert images[0].alt == "Product image"

    def test_images_without_alt(self) -> None:
        html = '<html><body><img src="/img.jpg"></body></html>'
        result = _parse(html)
        images = result.pages[0].images
        assert len(images) == 1
        assert images[0].src == "/img.jpg"
        assert images[0].alt is None

    def test_no_images(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].images == []


class TestLinks:
    def test_links_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        links = result.pages[0].links
        assert len(links) == 3
        assert links[0].text == "Home"
        assert links[0].href == "/"
        assert links[1].text == "Products"
        assert links[1].href == "/products"
        assert links[2].text == "Checkout"
        assert links[2].href == "/checkout"

    def test_no_links(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].links == []


class TestButtons:
    def test_buttons_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        buttons = result.pages[0].buttons
        assert len(buttons) == 1
        assert buttons[0].text == "Add to Cart"

    def test_input_buttons_extracted(self) -> None:
        html = '<html><body><input type="submit" value="Submit"></body></html>'
        result = _parse(html)
        buttons = result.pages[0].buttons
        assert len(buttons) == 1
        assert buttons[0].text == "Submit"

    def test_no_buttons(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].buttons == []


class TestForms:
    def test_forms_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        forms = result.pages[0].forms
        assert len(forms) == 1
        assert forms[0].action == "/submit"
        assert forms[0].method == "post"
        assert "name" in forms[0].input_names
        assert "email" in forms[0].input_names

    def test_no_forms(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].forms == []


class TestBreadcrumbs:
    def test_breadcrumbs_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        breadcrumbs = result.pages[0].breadcrumbs
        assert len(breadcrumbs) == 1
        assert breadcrumbs[0].items == ["Home", "Products", "Product Details"]

    def test_no_breadcrumbs(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].breadcrumbs == []


class TestFooter:
    def test_footer_extracted(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        footer = result.pages[0].footer
        assert footer is not None
        assert "\u00a9 2024 My Store" in footer.text or "My Store" in footer.text

    def test_no_footer(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].footer is None


class TestProvenance:
    def test_heading_provenance_preserved(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        heading = result.pages[0].headings[0]
        assert heading.provenance is not None
        assert heading.provenance.page_url == "https://example.com"
        assert heading.provenance.tag == "h1"
        assert heading.provenance.attributes == {}

    def test_link_provenance_preserved(self) -> None:
        html = _load_fixture("content-tech.html")
        result = _parse(html)
        link = result.pages[0].links[0]
        assert link.provenance is not None
        assert link.provenance.page_url == "https://example.com"
        assert link.provenance.tag == "a"
        assert link.provenance.attributes["href"] == "/"


class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        html = _load_fixture("content-tech.html")
        result1 = _parse(html)
        result2 = _parse(html)
        assert result1.pages[0].headings == result2.pages[0].headings
        assert result1.pages[0].paragraphs == result2.pages[0].paragraphs
        assert result1.pages[0].links == result2.pages[0].links


class TestEmptyPage:
    def test_empty_page_returns_empty_content(self) -> None:
        html = "<html><body></body></html>"
        result = _parse(html)
        page = result.pages[0]
        assert page.headings == []
        assert page.paragraphs == []
        assert page.lists == []
        assert page.tables == []
        assert page.images == []
        assert page.links == []
        assert page.buttons == []
        assert page.forms == []
        assert page.breadcrumbs == []
        assert page.footer is None
