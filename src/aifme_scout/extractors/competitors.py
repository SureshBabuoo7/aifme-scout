"""Competitor Discovery module.

Discovers competitors from explicit declarations, user-supplied lists,
and deterministic heuristic classification.
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

_COMPETITOR_DISCOVERY_DOMAINS: dict[str, list[str]] = {
    "e-commerce": [
        "amazon.com",
        "ebay.com",
        "etsy.com",
        "shopify.com",
        "woocommerce.com",
        "bigcommerce.com",
        "magento.com",
        "bigcartel.com",
        "ecwid.com",
        "squarespace.com/commerce",
    ],
    "saas": [
        "salesforce.com",
        "hubspot.com",
        "zendesk.com",
        "intercom.com",
        "mailchimp.com",
        "zoho.com",
        "freshworks.com",
        "pipedrive.com",
        "asana.com",
        "monday.com",
        "notion.so",
    ],
    "blog": [
        "wordpress.com",
        "medium.com",
        "substack.com",
        "blogger.com",
        "wix.com/blog",
        "squarespace.com/blog",
        "ghost.org",
        "joomla.org",
    ],
    "agency": [
        "clutch.co",
        "upwork.com",
        "fiverr.com",
        "99designs.com",
        "toptal.com",
        "crowdspring.com",
        "designhill.com",
    ],
    "media": [
        "youtube.com",
        "vimeo.com",
        "twitch.tv",
        "spotify.com",
        "soundcloud.com",
        "medium.com",
        "substack.com",
    ],
    "hosting": [
        "bluehost.com",
        "hostgator.com",
        "siteground.com",
        "dreamhost.com",
        "a2hosting.com",
        "inmotionhosting.com",
        "namecheap.com",
    ],
    "cms": [
        "wordpress.org",
        "drupal.org",
        "joomla.org",
        "craftcms.com",
        "contentful.com",
        "strapi.io",
    ],
    "ecommerce-platform": [
        "shopify.com",
        "woocommerce.com",
        "magento.com",
        "bigcommerce.com",
        "prestashop.com",
        "opencart.com",
    ],
    "developer-tools": [
        "gitlab.com",
        "bitbucket.org",
        "gitea.com",
        "sourceforge.net",
        "gitkraken.com",
    ],
}


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
        if href.startswith("http://") or href.startswith("https://"):
            absolute = href
        elif href.startswith("//"):
            parsed_base = urlparse(base_url)
            absolute = f"{parsed_base.scheme}:{href}"
        else:
            absolute = f"{base_url.rstrip('/')}/{href.lstrip('/')}"
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


def _discover_heuristic(
    parsed_site: ParsedSite,
    target_classification: str | None = None,
) -> list[Competitor]:
    """Discover competitors heuristically based on target classification.

    Heuristic discovery is best-effort and explicitly not authoritative.
    Only known competitor domains for the classified category are proposed.

    Args:
        parsed_site: Parsed site output from the HTML parser.
        target_classification: Optional classification from Summary Builder.

    Returns:
        List of heuristically discovered competitors.
    """
    if not target_classification or target_classification == "general":
        return []

    known_domains = _COMPETITOR_DISCOVERY_DOMAINS.get(target_classification, [])
    if not known_domains:
        return []

    base_domain = urlparse(parsed_site.target_url).netloc.lower()
    if base_domain.startswith("www."):
        base_domain = base_domain[4:]

    competitors: list[Competitor] = []
    for domain in known_domains:
        if domain == base_domain:
            continue
        name = _extract_name_from_url(f"https://{domain}")
        competitors.append(
            Competitor(
                name=name,
                url=f"https://{domain}",
                source="heuristic_discovery",
                discovery_method="HEURISTIC",
                confidence="medium",
                evidence=f"Heuristic competitor for {target_classification} category",
                provenance=None,
            )
        )

    return competitors


def resolve(
    parsed_site: ParsedSite,
    user_supplied: list[str] | None = None,
    target_classification: str | None = None,
) -> CompetitorResult:
    """Discover competitors from explicit declarations, user-supplied list,
    and deterministic heuristic classification.

    Discovery is evidence-driven. Explicit competitor references are
    discovered first. User-supplied competitors are included verbatim.
    Heuristic discovery uses target classification from the Summary
    Builder to propose known competitors for the classified category.

    Args:
        parsed_site: Parsed site output from the HTML parser.
        user_supplied: Optional list of user-supplied competitor URLs.
        target_classification: Optional classification from Summary Builder
            used for heuristic competitor discovery.

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
    heuristic_competitors = _discover_heuristic(parsed_site, target_classification)

    all_competitors = user_competitors + explicit_competitors + heuristic_competitors
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
            page_competitors.extend(
                c for c in heuristic_competitors if c.source == "heuristic_discovery"
            )
        pages.append(CompetitorPageResult(url=parsed_page.url, competitors=page_competitors))

    heuristic_status = "COMPLETED" if heuristic_competitors else "NOT_APPLICABLE"

    return CompetitorResult(
        target_url=parsed_site.target_url,
        pages=pages,
        user_supplied=user_competitors,
        heuristic_discovery_status=heuristic_status,
    )
