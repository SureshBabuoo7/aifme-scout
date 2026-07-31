"""HTML Parser module.

Converts raw HTML into a deterministic, navigable DOM tree.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from bs4.element import Tag

from aifme_scout.parser.models import Element, ParsedPage, ParsedSite, ParseError, ParseWarning
from aifme_scout.scanner.models import RawSite


def _tag_to_element(tag: Tag, parent: Element | None = None) -> Element:
    attrs: dict[str, str] = {}
    for key, value in tag.attrs.items():
        if isinstance(key, str):
            if isinstance(value, list):
                attrs[key] = " ".join(str(v) for v in value)
            else:
                attrs[key] = str(value)

    text = tag.get_text(strip=True)
    children = [
        _tag_to_element(child, parent=None) for child in tag.children if isinstance(child, Tag)
    ]
    element = Element(tag.name or "", attrs, text, children, parent)
    for child in children:
        child._parent = element
    return element


def _soup_to_element(soup: BeautifulSoup) -> Element:
    children = [_tag_to_element(child) for child in soup.children if isinstance(child, Tag)]
    return Element("[document]", {}, soup.get_text(strip=True), children)


def parse(raw_site: RawSite) -> ParsedSite:
    """Parse a RawSite into a ParsedSite.

    This is a pure function over RawSite. Malformed HTML is recovered
    leniently; individual page failures are flagged, never raised.
    """
    pages: list[ParsedPage] = []
    parse_errors: list[ParseError] = []

    for page in raw_site.pages:
        try:
            soup = BeautifulSoup(page.html, "html.parser")
            root = _soup_to_element(soup)
            head = root.find("head")
            body = root.find("body")
            warnings: list[ParseWarning] = []
            if head is None:
                warnings.append(ParseWarning(message="Missing <head> tag", severity="warning"))
            if body is None:
                warnings.append(ParseWarning(message="Missing <body> tag", severity="warning"))
            pages.append(
                ParsedPage(
                    url=page.url,
                    raw_html=page.html,
                    root=root,
                    head=head,
                    body=body,
                    warnings=warnings,
                )
            )
        except Exception as exc:
            parse_errors.append(ParseError(code="parse_failure", message=str(exc), url=page.url))

    return ParsedSite(target_url=raw_site.target_url, pages=pages, parse_errors=parse_errors)
