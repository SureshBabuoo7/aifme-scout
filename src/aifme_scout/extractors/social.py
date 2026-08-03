"""Social Discovery module.

Finds linked social profiles from ParsedSite.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from aifme_scout.extractors.models import (
    SocialPageResult,
    SocialProfile,
    SocialProfileProvenance,
    SocialResult,
)
from aifme_scout.parser.models import Element, ParsedSite

if TYPE_CHECKING:
    pass


PLATFORM_DOMAINS = {
    "linkedin.com": "LinkedIn",
    "twitter.com": "X",
    "x.com": "X",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "instagram.com": "Instagram",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "tiktok.com": "TikTok",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "discord.com": "Discord",
    "discord.gg": "Discord",
    "reddit.com": "Reddit",
    "pinterest.com": "Pinterest",
    "threads.net": "Threads",
    "medium.com": "Medium",
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


def _extract_username(url: str, platform: str) -> str | None:
    """Extract username from social profile URL."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return None
    parts = path.split("/")
    if len(parts) >= 1 and parts[0]:
        return parts[0]
    return None


def _detect_platform(url: str) -> str | None:
    """Detect platform from URL domain."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    for platform_domain, platform_name in PLATFORM_DOMAINS.items():
        if domain == platform_domain or domain.endswith(f".{platform_domain}"):
            return platform_name
    return None


def _create_provenance(
    element: Element, page_url: str, attribute: str = "href"
) -> SocialProfileProvenance:
    """Create provenance for a discovered social profile."""
    return SocialProfileProvenance(
        page_url=page_url,
        dom_path=_build_dom_path(element),
        tag=element.tag,
        attribute=attribute,
        original_url=element.get("href") or "",
    )


def _collect_links(root: Element | None) -> list[tuple[Element, str]]:
    """Collect all links from the DOM tree."""
    if root is None:
        return []
    links: list[tuple[Element, str]] = []
    for element in root.find_all("a"):
        href = element.get("href", "")
        if href:
            links.append((element, href))
    return links


def _normalize_url(url: str, base_url: str) -> str | None:
    """Normalize relative URLs to absolute URLs."""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("//"):
        parsed_base = urlparse(base_url)
        return f"{parsed_base.scheme}:{url}"
    if url.startswith("#"):
        return None
    if url.startswith("mailto:") or url.startswith("tel:"):
        return None
    parsed_base = urlparse(base_url)
    return f"{parsed_base.scheme}://{parsed_base.netloc}/{url.lstrip('/')}"


def discover(parsed_site: ParsedSite) -> SocialResult:
    """Discover social profiles from a ParsedSite.

    Detection is deterministic and evidence-driven. Only explicitly
    linked social profiles are reported. No inference or guessing is
    performed.

    Args:
        parsed_site: Parsed site output from the HTML parser.

    Returns:
        SocialResult with per-page discovered social profiles.
    """
    pages: list[SocialPageResult] = []

    for parsed_page in parsed_site.pages:
        profiles: list[SocialProfile] = []
        seen_urls: set[str] = set()

        links = _collect_links(parsed_page.root)
        for element, href in links:
            normalized = _normalize_url(href, parsed_page.url)
            if normalized is None:
                continue
            platform = _detect_platform(normalized)
            if platform is None:
                continue
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)

            username = _extract_username(normalized, platform)
            profiles.append(
                SocialProfile(
                    platform=platform,
                    url=normalized,
                    username=username,
                    detection_method="link",
                    provenance=_create_provenance(element, parsed_page.url),
                )
            )

        pages.append(SocialPageResult(url=parsed_page.url, profiles=profiles))

    return SocialResult(target_url=parsed_site.target_url, pages=pages)
