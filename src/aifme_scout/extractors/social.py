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
    "bsky.app": "Bluesky",
    "bsky.social": "Bluesky",
    "mastodon.social": "Mastodon",
    "mastodon.online": "Mastodon",
    "twitch.tv": "Twitch",
    "snapchat.com": "Snapchat",
    "wa.me": "WhatsApp",
    "whatsapp.com": "WhatsApp",
    "t.me": "Telegram",
    "telegram.me": "Telegram",
    "behance.net": "Behance",
    "dribbble.com": "Dribbble",
    "flickr.com": "Flickr",
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

        icon_platforms = _detect_social_icons(parsed_page.root, parsed_page.url)
        for profile in icon_platforms:
            if profile.url not in seen_urls:
                seen_urls.add(profile.url)
                profiles.append(profile)

        json_ld_profiles = _detect_json_ld_social(parsed_page.root, parsed_page.url)
        for profile in json_ld_profiles:
            if profile.url not in seen_urls:
                seen_urls.add(profile.url)
                profiles.append(profile)

        pages.append(SocialPageResult(url=parsed_page.url, profiles=profiles))

    return SocialResult(target_url=parsed_site.target_url, pages=pages)


_ICON_PLATFORM_CLASSES = {
    "fa-linkedin": "LinkedIn",
    "fa-x-twitter": "X",
    "fa-twitter": "X",
    "fa-facebook": "Facebook",
    "fa-instagram": "Instagram",
    "fa-youtube": "YouTube",
    "fa-tiktok": "TikTok",
    "fa-github": "GitHub",
    "fa-gitlab": "GitLab",
    "fa-discord": "Discord",
    "fa-reddit": "Reddit",
    "fa-pinterest": "Pinterest",
    "fa-medium": "Medium",
    "fa-bsky": "Bluesky",
    "fa-mastodon": "Mastodon",
    "fa-twitch": "Twitch",
    "fa-snapchat": "Snapchat",
    "fa-whatsapp": "WhatsApp",
    "fa-telegram": "Telegram",
    "fa-behance": "Behance",
    "fa-dribbble": "Dribbble",
    "fa-flickr": "Flickr",
    "fa-tiktok": "TikTok",
}


def _detect_social_icons(root: Element | None, page_url: str) -> list[SocialProfile]:
    """Detect social profiles via icon class names."""
    if root is None:
        return []
    profiles: list[SocialProfile] = []
    seen_platforms: set[str] = set()

    for elem in root.find_all(True):
        class_attr = elem.get("class", "")
        if not class_attr:
            continue
        classes = class_attr.split() if isinstance(class_attr, str) else list(class_attr)
        for cls in classes:
            cls_lower = cls.lower()
            if cls_lower in _ICON_PLATFORM_CLASSES:
                platform = _ICON_PLATFORM_CLASSES[cls_lower]
                if platform not in seen_platforms:
                    seen_platforms.add(platform)
                    href = elem.get("href", "")
                    url = href if href and (href.startswith("http://") or href.startswith("https://")) else ""
                    profiles.append(
                        SocialProfile(
                            platform=platform,
                            url=url or page_url,
                            username=None,
                            detection_method="icon_class",
                            provenance=SocialProfileProvenance(
                                page_url=page_url,
                                dom_path="/",
                                tag=elem.tag,
                                attribute="class",
                                original_url=url,
                            ),
                        )
                    )
                break

    return profiles


def _detect_json_ld_social(root: Element | None, page_url: str) -> list[SocialProfile]:
    """Detect social profiles from JSON-LD sameAs."""
    import json
    import re as _re

    if root is None:
        return []
    profiles: list[SocialProfile] = []
    seen_urls: set[str] = set()

    for script in root.find_all("script", {"type": "application/ld+json"}):
        raw = script.text or script.string or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            json_text = _re.sub(r'/\*.*?\*/', '', raw, flags=_re.DOTALL)
            json_text = _re.sub(r'(?<!\S)//.*?$', '', json_text, flags=_re.MULTILINE)
            data = json.loads(json_text)
        except Exception:
            try:
                data = json.loads(raw)
            except Exception:
                continue

        def extract_same_as(node: object) -> None:
            if isinstance(node, dict):
                same_as = node.get("sameAs")
                if isinstance(same_as, list):
                    for url in same_as:
                        if isinstance(url, str) and url.startswith("http"):
                            platform = _detect_platform(url)
                            if platform and url not in seen_urls:
                                seen_urls.add(url)
                                profiles.append(
                                    SocialProfile(
                                        platform=platform,
                                        url=url,
                                        username=_extract_username(url, platform),
                                        detection_method="json_ld",
                                        provenance=SocialProfileProvenance(
                                            page_url=page_url,
                                            dom_path="/",
                                            tag="script",
                                            attribute="type",
                                            original_url=url,
                                        ),
                                    )
                                )
                for value in node.values():
                    extract_same_as(value)
            elif isinstance(node, list):
                for item in node:
                    extract_same_as(item)

        extract_same_as(data)

    return profiles
