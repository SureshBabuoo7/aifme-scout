"""Content Extractor module.

Pulls structured content from the parsed body region.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aifme_scout.extractors.models import (
    ContentBreadcrumb,
    ContentButton,
    ContentElementProvenance,
    ContentFooter,
    ContentForm,
    ContentHeading,
    ContentImage,
    ContentLink,
    ContentList,
    ContentListItem,
    ContentPageResult,
    ContentParagraph,
    ContentResult,
    ContentTable,
)
from aifme_scout.parser.models import Element, ParsedSite

if TYPE_CHECKING:
    pass


def _text_content(element: Element | None) -> str:
    """Get the text content of an element, stripping whitespace."""
    if element is None:
        return ""
    return " ".join(element.text.split())


def _create_provenance(element: Element, page_url: str) -> ContentElementProvenance:
    """Create provenance for an extracted element."""
    return ContentElementProvenance(
        page_url=page_url,
        dom_path=_build_dom_path(element),
        tag=element.tag,
        attributes=element.attrs,
        original_text=element.text[:200] if element.text else None,
    )


def _build_dom_path(element: Element | None) -> str:
    """Build a simple DOM path for provenance."""
    if element is None or element.parent is None:
        return "/"
    parent_path = _build_dom_path(element.parent)
    tag = element.tag
    siblings = [child for child in element.parent.children if child.tag == tag]
    if len(siblings) > 1:
        index = siblings.index(element) + 1
        return f"{parent_path}/{tag}[{index}]"
    return f"{parent_path}/{tag}"


def _extract_headings(body: Element | None, page_url: str) -> list[ContentHeading]:
    """Extract headings from the body."""
    if body is None:
        return []
    headings: list[ContentHeading] = []
    for level in range(1, 7):
        for heading in body.find_all(f"h{level}"):
            text = _text_content(heading)
            if text:
                headings.append(
                    ContentHeading(
                        level=level,
                        text=text,
                        provenance=_create_provenance(heading, page_url),
                    )
                )
    return headings


def _extract_paragraphs(body: Element | None, page_url: str) -> list[ContentParagraph]:
    """Extract paragraphs from the body."""
    if body is None:
        return []
    paragraphs: list[ContentParagraph] = []
    for p in body.find_all("p"):
        text = _text_content(p)
        if text:
            paragraphs.append(
                ContentParagraph(
                    text=text,
                    provenance=_create_provenance(p, page_url),
                )
            )
    return paragraphs


def _extract_lists(body: Element | None, page_url: str) -> list[ContentList]:
    """Extract lists from the body."""
    if body is None:
        return []
    lists: list[ContentList] = []
    for list_elem in body.find_all("ul"):
        lists.extend(_process_list(list_elem, "ul", page_url))
    for list_elem in body.find_all("ol"):
        lists.extend(_process_list(list_elem, "ol", page_url))
    return lists


def _process_list(list_elem: Element, list_type: str, page_url: str) -> list[ContentList]:
    """Process a single list element."""
    items: list[ContentListItem] = []
    for li in list_elem.find_all("li"):
        text = _text_content(li)
        if text:
            items.append(
                ContentListItem(
                    text=text,
                    provenance=_create_provenance(li, page_url),
                )
            )
    if items:
        return [
            ContentList(
                list_type=list_type,
                items=items,
                provenance=_create_provenance(list_elem, page_url),
            )
        ]
    return []


def _extract_tables(body: Element | None, page_url: str) -> list[ContentTable]:
    """Extract tables from the body."""
    if body is None:
        return []
    tables: list[ContentTable] = []
    for table in body.find_all("table"):
        headers: list[str] = []
        for th in table.find_all("th"):
            text = _text_content(th)
            if text:
                headers.append(text)

        rows: list[list[str]] = []
        for tr in table.find_all("tr"):
            row: list[str] = []
            for td in tr.find_all("td"):
                text = _text_content(td)
                if text:
                    row.append(text)
            if row:
                rows.append(row)

        if headers or rows:
            tables.append(
                ContentTable(
                    headers=headers,
                    rows=rows,
                    provenance=_create_provenance(table, page_url),
                )
            )
    return tables


def _extract_images(body: Element | None, page_url: str) -> list[ContentImage]:
    """Extract images from the body."""
    if body is None:
        return []
    images: list[ContentImage] = []
    for img in body.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt")
        if src:
            images.append(
                ContentImage(
                    src=src,
                    alt=alt,
                    provenance=_create_provenance(img, page_url),
                )
            )
    return images


def _extract_links(body: Element | None, page_url: str) -> list[ContentLink]:
    """Extract links from the body."""
    if body is None:
        return []
    links: list[ContentLink] = []
    for a in body.find_all("a"):
        href = a.get("href", "")
        text = _text_content(a)
        if href:
            links.append(
                ContentLink(
                    text=text,
                    href=href,
                    provenance=_create_provenance(a, page_url),
                )
            )
    return links


def _extract_buttons(body: Element | None, page_url: str) -> list[ContentButton]:
    """Extract buttons from the body."""
    if body is None:
        return []
    buttons: list[ContentButton] = []
    for button in body.find_all("button"):
        text = _text_content(button)
        if text:
            buttons.append(
                ContentButton(
                    text=text,
                    provenance=_create_provenance(button, page_url),
                )
            )
    for input_elem in body.find_all("input"):
        input_type = input_elem.get("type", "")
        if input_type in ("submit", "button", "reset"):
            text = input_elem.get("value") or ""
            if text:
                buttons.append(
                    ContentButton(
                        text=text,
                        provenance=_create_provenance(input_elem, page_url),
                    )
                )
    return buttons


def _extract_forms(body: Element | None, page_url: str) -> list[ContentForm]:
    """Extract forms from the body."""
    if body is None:
        return []
    forms: list[ContentForm] = []
    for form in body.find_all("form"):
        action = form.get("action", "")
        method = form.get("method", "")
        input_names: list[str] = []
        for input_elem in form.find_all("input"):
            name = input_elem.get("name", "")
            if name:
                input_names.append(name)

        forms.append(
            ContentForm(
                action=action or None,
                method=method or None,
                input_names=input_names,
                provenance=_create_provenance(form, page_url),
            )
        )
    return forms


def _extract_breadcrumbs(body: Element | None, page_url: str) -> list[ContentBreadcrumb]:
    """Extract breadcrumbs from the body."""
    if body is None:
        return []
    breadcrumbs: list[ContentBreadcrumb] = []
    for nav in body.find_all("nav"):
        if nav.get("aria-label") == "breadcrumb":
            items: list[str] = []
            for li in nav.find_all("li"):
                text = _text_content(li)
                if text:
                    items.append(text)
            if items:
                breadcrumbs.append(
                    ContentBreadcrumb(
                        items=items,
                        provenance=_create_provenance(nav, page_url),
                    )
                )
    return breadcrumbs


def _extract_footer(body: Element | None, page_url: str) -> ContentFooter | None:
    """Extract footer content from the body."""
    if body is None:
        return None
    footer = body.find("footer")
    if footer is None:
        return None
    text = _text_content(footer)
    if text:
        return ContentFooter(
            text=text,
            provenance=_create_provenance(footer, page_url),
        )
    return None


def extract(parsed_site: ParsedSite) -> ContentResult:
    """Extract structured content from a ParsedSite.

    Args:
        parsed_site: Parsed site from the HTML Parser.

    Returns:
        ContentResult with per-page extracted content.
    """
    pages: list[ContentPageResult] = []

    for parsed_page in parsed_site.pages:
        body = parsed_page.body
        page_url = parsed_page.url

        headings = _extract_headings(body, page_url)
        paragraphs = _extract_paragraphs(body, page_url)
        lists = _extract_lists(body, page_url)
        tables = _extract_tables(body, page_url)
        images = _extract_images(body, page_url)
        links = _extract_links(body, page_url)
        buttons = _extract_buttons(body, page_url)
        forms = _extract_forms(body, page_url)
        breadcrumbs = _extract_breadcrumbs(body, page_url)
        footer = _extract_footer(body, page_url)

        pages.append(
            ContentPageResult(
                url=page_url,
                headings=headings,
                paragraphs=paragraphs,
                lists=lists,
                tables=tables,
                images=images,
                links=links,
                buttons=buttons,
                forms=forms,
                breadcrumbs=breadcrumbs,
                footer=footer,
            )
        )

    return ContentResult(target_url=parsed_site.target_url, pages=pages)
