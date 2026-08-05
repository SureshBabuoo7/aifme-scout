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


def _extract_contact_emails(body: Element | None, page_url: str) -> list[str]:
    """Extract email addresses from mailto: links."""
    if body is None:
        return []
    emails: list[str] = []
    for a in body.find_all("a"):
        href = a.get("href", "")
        if href.lower().startswith("mailto:"):
            email = href[7:].split("?")[0].strip()
            if email and email not in emails:
                emails.append(email)
    return emails


def _extract_contact_phones(body: Element | None, page_url: str) -> list[str]:
    """Extract phone numbers from tel: links."""
    if body is None:
        return []
    phones: list[str] = []
    for a in body.find_all("a"):
        href = a.get("href", "")
        if href.lower().startswith("tel:"):
            phone = href[4:].strip()
            if phone and phone not in phones:
                phones.append(phone)
    return phones


def _extract_videos(body: Element | None, page_url: str) -> list[dict]:
    """Extract video and iframe (YouTube/Vimeo) sources."""
    if body is None:
        return []
    videos: list[dict] = []
    seen: set[str] = set()
    for video in body.find_all("video"):
        src = video.get("src", "")
        if src and src not in seen:
            seen.add(src)
            videos.append({"type": "video", "src": src})
    for iframe in body.find_all("iframe"):
        src = iframe.get("src", "")
        if not src:
            continue
        src_lower = src.lower()
        if "youtube" in src_lower or "youtu.be" in src_lower or "vimeo" in src_lower:
            if src not in seen:
                seen.add(src)
                platform = "youtube" if "youtube" in src_lower or "youtu.be" in src_lower else "vimeo"
                videos.append({"type": "iframe", "platform": platform, "src": src})
    return videos


def _extract_audio(body: Element | None, page_url: str) -> list[str]:
    """Extract audio sources."""
    if body is None:
        return []
    sources: list[str] = []
    seen: set[str] = set()
    for audio in body.find_all("audio"):
        src = audio.get("src", "")
        if src and src not in seen:
            seen.add(src)
            sources.append(src)
        for source in audio.find_all("source"):
            src = source.get("src", "")
            if src and src not in seen:
                seen.add(src)
                sources.append(src)
    return sources


def _extract_blockquotes(body: Element | None, page_url: str) -> list[str]:
    """Extract blockquote text content."""
    if body is None:
        return []
    quotes: list[str] = []
    for bq in body.find_all("blockquote"):
        text = _text_content(bq)
        if text:
            quotes.append(text)
    return quotes


def _extract_code_blocks(body: Element | None, page_url: str) -> list[dict]:
    """Extract code block content from <pre> and <code> tags."""
    if body is None:
        return []
    blocks: list[dict] = []
    seen_texts: set[str] = set()
    for pre in body.find_all("pre"):
        code = pre.find("code")
        text = _text_content(code) if code is not None else _text_content(pre)
        if text and text not in seen_texts:
            seen_texts.add(text)
            blocks.append({"tag": "pre", "text": text})
    for code in body.find_all("code"):
        if code.parent and code.parent.tag == "pre":
            continue
        text = _text_content(code)
        if text and text not in seen_texts:
            seen_texts.add(text)
            blocks.append({"tag": "code", "text": text})
    return blocks


def _extract_definition_lists(body: Element | None, page_url: str) -> list[dict]:
    """Extract definition list terms and descriptions."""
    if body is None:
        return []
    dl_items: list[dict] = []
    for dl in body.find_all("dl"):
        dts = dl.find_all("dt")
        dds = dl.find_all("dd")
        terms = [_text_content(dt) for dt in dts if _text_content(dt)]
        descriptions = [_text_content(dd) for dd in dds if _text_content(dd)]
        if terms or descriptions:
            dl_items.append({"terms": terms, "descriptions": descriptions})
    return dl_items


def _extract_address(body: Element | None, page_url: str) -> str | None:
    """Extract contact address from <address> tag."""
    if body is None:
        return None
    address = body.find("address")
    if address is None:
        return None
    text = _text_content(address)
    return text if text else None


def _extract_figure_captions(body: Element | None, page_url: str) -> list[dict]:
    """Extract figure captions."""
    if body is None:
        return []
    captions: list[dict] = []
    for figure in body.find_all("figure"):
        figcaption = figure.find("figcaption")
        caption_text = _text_content(figcaption) if figcaption is not None else None
        img = figure.find("img")
        img_src = img.get("src", "") if img is not None else ""
        captions.append(
            {"image_src": img_src, "caption": caption_text}
            if caption_text
            else {"image_src": img_src}
        )
    return captions


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
        contact_emails = _extract_contact_emails(body, page_url)
        contact_phones = _extract_contact_phones(body, page_url)
        videos = _extract_videos(body, page_url)
        audios = _extract_audio(body, page_url)
        blockquotes = _extract_blockquotes(body, page_url)
        code_blocks = _extract_code_blocks(body, page_url)
        definition_lists = _extract_definition_lists(body, page_url)
        address = _extract_address(body, page_url)
        figure_captions = _extract_figure_captions(body, page_url)

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
                contact_emails=contact_emails,
                contact_phones=contact_phones,
                videos=videos,
                audios=audios,
                blockquotes=blockquotes,
                code_blocks=code_blocks,
                definition_lists=definition_lists,
                address=address,
                figure_captions=figure_captions,
            )
        )

    return ContentResult(target_url=parsed_site.target_url, pages=pages)
