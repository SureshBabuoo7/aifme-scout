"""Competitor Discovery module.

Discovers competitors from explicit declarations and user-supplied lists.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from aifme_scout.extractors.models import (
    Competitor,
    CompetitorPageResult,
    CompetitorProvenance,
    CompetitorResult,
)
from aifme_scout.parser.models import Element, ParsedSite

if TYPE_CHECKING:
    pass


_COMPETITOR_PAGE_KEYWORDS = re.compile(
    r"alternatives|competitors|comparison|compare|partners|versus|vs\.?|vs$",
    re.IGNORECASE,
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


def _create_provenance(
    element: Element, page_url: str, original_text: str | None = None
) -> CompetitorProvenance:
    """Create provenance for a discovered competitor."""
    return CompetitorProvenance(
        page_url=page_url,
        dom_path=_build_dom_path(element),
        tag=element.tag,
        attribute="href",
        original_text=original_text,
        original_url=element.get("href") or None,
    )


def _is_competitor_page(page_url: str, root: Element | None) -> bool:
    """Check if a page appears to be a competitor/comparison page."""
    if root is None:
        return False

    title = root.find("title")
    title_text = title.text if title is not None else ""

    heading_texts: list[str] = []
    for level in range(1, 7):
        for heading in root.find_all(f"h{level}"):
            if heading.text:
                heading_texts.append(heading.text)

    combined_text = f"{title_text} {' '.join(heading_texts)}"
    return bool(_COMPETITOR_PAGE_KEYWORDS.search(combined_text))


def _extract_external_links(root: Element | None, base_url: str) -> list[tuple[Element, str, str]]:
    """Extract external links from the DOM."""
    if root is None:
        return []
    links: list[tuple[Element, str, str]] = []
    base_domain = urlparse(base_url).netloc.lower()
    if base_domain.startswith("www."):
        base_domain = base_domain[4:]

    for a in root.find_all("a"):
        href = a.get("href", "")
        if not href:
            continue
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        absolute = href if href.startswith("http") else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
        parsed = urlparse(absolute)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain and domain != base_domain:
            text = a.text.strip()
            links.append((a, absolute, text))
    return links


def _extract_name_from_url(url: str) -> str:
    """Extract a display name from a URL."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    parts = domain.split(".")
    if parts:
        return parts[0].capitalize()
    return domain


def _discover_explicit(parsed_site: ParsedSite) -> list[Competitor]:
    """Discover competitors from explicit declarations on the site."""
    competitors: list[Competitor] = []
    seen_urls: set[str] = set()

    for parsed_page in parsed_site.pages:
        if not _is_competitor_page(parsed_page.url, parsed_page.root):
            continue

        links = _extract_external_links(parsed_page.root, parsed_page.url)
        for element, absolute_url, text in links:
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            name = text if text else _extract_name_from_url(absolute_url)
            competitors.append(
                Competitor(
                    name=name,
                    url=absolute_url,
                    source=parsed_page.url,
                    discovery_method="EXPLICIT_DECLARATION",
                    confidence="high",
                    evidence=f"Found on competitor/comparison page: {parsed_page.url}",
                    provenance=_create_provenance(element, parsed_page.url, text),
                )
            )

    return competitors


def resolve(
    parsed_site: ParsedSite,
    user_supplied: list[str] | None = None,
) -> CompetitorResult:
    """Discover competitors from explicit declarations and user-supplied list.

    Discovery is deterministic and evidence-driven. Only explicit competitor
    references are discovered. Heuristic discovery is intentionally deferred.

    Args:
        parsed_site: Parsed site output from the HTML parser.
        user_supplied: Optional list of user-supplied competitor URLs.

    Returns:
        CompetitorResult with discovered competitors.
    """
    pages: list[CompetitorPageResult] = []
    user_competitors: list[Competitor] = []

    if user_supplied:
        for url in user_supplied:
            name = _extract_name_from_url(url)
            user_competitors.append(
                Competitor(
                    name=name,
                    url=url,
                    source="user_supplied",
                    discovery_method="USER_SUPPLIED",
                    confidence="high",
                    evidence="User-supplied competitor",
                )
            )

    explicit_competitors = _discover_explicit(parsed_site)

    all_competitors = user_competitors + explicit_competitors
    seen_urls: set[str] = set()
    deduplicated: list[Competitor] = []
    for competitor in all_competitors:
        if competitor.url and competitor.url in seen_urls:
            continue
        if competitor.url:
            seen_urls.add(competitor.url)
        deduplicated.append(competitor)

    for parsed_page in parsed_site.pages:
        page_competitors = [c for c in deduplicated if c.source == parsed_page.url]
        if parsed_page == parsed_site.pages[0]:
            page_competitors.extend(user_competitors)
        pages.append(CompetitorPageResult(url=parsed_page.url, competitors=page_competitors))

    return CompetitorResult(
        target_url=parsed_site.target_url,
        pages=pages,
        user_supplied=user_competitors,
        heuristic_discovery_status="DEFERRED",
    )
