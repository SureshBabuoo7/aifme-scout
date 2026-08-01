"""Technology Detector module.

Identifies technologies from deterministic evidence in ParsedSite and RawSite.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from aifme_scout.extractors.models import (
    Technology,
    TechnologyEvidence,
    TechnologyPageResult,
    TechnologyResult,
)
from aifme_scout.parser.models import Element, ParsedPage, ParsedSite
from aifme_scout.scanner.models import RawPage, RawSite

if TYPE_CHECKING:
    pass


def _evidence(page_url: str, rule: str, matched_value: str, source: str) -> TechnologyEvidence:
    """Create a TechnologyEvidence instance."""
    return TechnologyEvidence(
        page_url=page_url,
        detection_rule=rule,
        matched_value=matched_value,
        source=source,
    )


def _deduplicate(technologies: list[Technology]) -> list[Technology]:
    """Deduplicate technologies by name, merging evidence."""
    seen: dict[str, Technology] = {}
    for tech in technologies:
        if tech.name in seen:
            existing = seen[tech.name]
            merged_evidence = list(existing.evidence) + list(tech.evidence)
            confidence = existing.confidence
            if tech.confidence == "high":
                confidence = "high"
            version = existing.version or tech.version
            seen[tech.name] = Technology(
                name=tech.name,
                category=tech.category,
                version=version,
                confidence=confidence,
                detection_method=tech.detection_method,
                evidence=merged_evidence,
            )
        else:
            seen[tech.name] = tech
    return list(seen.values())


def _check_meta_generator(page: ParsedPage) -> list[Technology]:
    """Check for generator meta tags."""
    technologies: list[Technology] = []
    head = page.head
    if head is None:
        return technologies

    for meta in head.find_all("meta"):
        name = meta.get("name", "")
        content = meta.get("content", "")
        if name != "generator" or not content:
            continue

        generator_lower = content.lower()

        if "wordpress" in generator_lower:
            version = None
            match = re.search(r"wordpress\s+([\d.]+)", content, re.IGNORECASE)
            if match:
                version = match.group(1)
            technologies.append(
                Technology(
                    name="WordPress",
                    category="CMS",
                    version=version,
                    confidence="high",
                    detection_method="meta_generator",
                    evidence=[_evidence(page.url, "meta_generator_wordpress", content, "meta")],
                )
            )
        elif "drupal" in generator_lower:
            version = None
            match = re.search(r"drupal\s+([\d.]+)", content, re.IGNORECASE)
            if match:
                version = match.group(1)
            technologies.append(
                Technology(
                    name="Drupal",
                    category="CMS",
                    version=version,
                    confidence="high",
                    detection_method="meta_generator",
                    evidence=[_evidence(page.url, "meta_generator_drupal", content, "meta")],
                )
            )
        elif "joomla" in generator_lower:
            version = None
            match = re.search(r"joomla!\s+([\d.]+)", content, re.IGNORECASE)
            if match:
                version = match.group(1)
            technologies.append(
                Technology(
                    name="Joomla",
                    category="CMS",
                    version=version,
                    confidence="high",
                    detection_method="meta_generator",
                    evidence=[_evidence(page.url, "meta_generator_joomla", content, "meta")],
                )
            )
        elif "ghost" in generator_lower:
            technologies.append(
                Technology(
                    name="Ghost",
                    category="CMS",
                    confidence="high",
                    detection_method="meta_generator",
                    evidence=[_evidence(page.url, "meta_generator_ghost", content, "meta")],
                )
            )

    return technologies


def _collect_element_attr_values(root: Element | None, tag: str, attr: str) -> list[str]:
    """Collect attribute values from all elements with a given tag."""
    if root is None:
        return []
    values: list[str] = []
    for element in root.find_all(tag):
        value = element.get(attr)
        if value:
            values.append(value)
    return values


def _find_by_attribute(
    element: Element | None, attr: str, value: str | None = None
) -> Element | None:
    """Find an element by attribute, searching recursively."""
    if element is None:
        return None
    if value is not None:
        if element.get(attr) == value:
            return element
    else:
        if element.get(attr) is not None:
            return element
    for child in element.children:
        found = _find_by_attribute(child, attr, value)
        if found is not None:
            return found
    return None


def _check_script_urls(page: ParsedPage) -> list[Technology]:
    """Check script URLs for technology fingerprints."""
    technologies: list[Technology] = []
    srcs = _collect_element_attr_values(page.root, "script", "src")

    for src in srcs:
        src_lower = src.lower()

        # Next.js
        if "/_next/static/" in src_lower:
            technologies.append(
                Technology(
                    name="Next.js",
                    category="Framework",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_nextjs", src, "script")],
                )
            )
            continue

        # Nuxt
        if "/_nuxt/" in src_lower:
            technologies.append(
                Technology(
                    name="Nuxt",
                    category="Framework",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_nuxt", src, "script")],
                )
            )
            continue

        # Google Analytics
        if "google-analytics.com" in src_lower or "googletagmanager.com/gtag" in src_lower:
            technologies.append(
                Technology(
                    name="Google Analytics",
                    category="Analytics",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_google_analytics", src, "script")],
                )
            )
            continue

        # Google Tag Manager
        if "googletagmanager.com/gtm" in src_lower:
            technologies.append(
                Technology(
                    name="Google Tag Manager",
                    category="Analytics",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_google_tag_manager", src, "script")],
                )
            )
            continue

        # Plausible
        if "plausible.io" in src_lower or "plausible.js" in src_lower:
            technologies.append(
                Technology(
                    name="Plausible",
                    category="Analytics",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_plausible", src, "script")],
                )
            )
            continue

        # Matomo
        if "matomo.php" in src_lower or "piwik.php" in src_lower:
            technologies.append(
                Technology(
                    name="Matomo",
                    category="Analytics",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_matomo", src, "script")],
                )
            )
            continue

        # React
        if ("react" in src_lower and "react-" in src_lower) or (
            "react." in src_lower and ".js" in src_lower
        ):
            technologies.append(
                Technology(
                    name="React",
                    category="Framework",
                    confidence="medium",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_react", src, "script")],
                )
            )
            continue

        # Vue
        if "vue" in src_lower and ("vue." in src_lower or "vue-" in src_lower):
            technologies.append(
                Technology(
                    name="Vue",
                    category="Framework",
                    confidence="medium",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_vue", src, "script")],
                )
            )
            continue

        # Angular
        if "angular" in src_lower:
            technologies.append(
                Technology(
                    name="Angular",
                    category="Framework",
                    confidence="medium",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_angular", src, "script")],
                )
            )
            continue

        # Svelte
        if "svelte" in src_lower:
            technologies.append(
                Technology(
                    name="Svelte",
                    category="Framework",
                    confidence="medium",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_svelte", src, "script")],
                )
            )
            continue

        # Bootstrap JS
        if "bootstrap" in src_lower and src_lower.endswith(".js"):
            technologies.append(
                Technology(
                    name="Bootstrap",
                    category="CSS Framework",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_bootstrap", src, "script")],
                )
            )
            continue

        # Tailwind CSS (JS build tool or CDN)
        if "tailwindcss" in src_lower:
            technologies.append(
                Technology(
                    name="Tailwind CSS",
                    category="CSS Framework",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_tailwindcss", src, "script")],
                )
            )
            continue

        # Shopify
        if "shopify" in src_lower:
            technologies.append(
                Technology(
                    name="Shopify",
                    category="E-commerce",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_shopify", src, "script")],
                )
            )
            continue

        # Wix
        if "wix" in src_lower:
            technologies.append(
                Technology(
                    name="Wix",
                    category="Website Builder",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_wix", src, "script")],
                )
            )
            continue

        # Squarespace
        if "squarespace" in src_lower:
            technologies.append(
                Technology(
                    name="Squarespace",
                    category="Website Builder",
                    confidence="high",
                    detection_method="script_url",
                    evidence=[_evidence(page.url, "script_url_squarespace", src, "script")],
                )
            )
            continue

    return technologies


def _check_link_urls(page: ParsedPage) -> list[Technology]:
    """Check link URLs for technology fingerprints."""
    technologies: list[Technology] = []
    if page.head is None:
        return technologies

    hrefs = _collect_element_attr_values(page.head, "link", "href")

    for href in hrefs:
        href_lower = href.lower()

        if "bootstrap" in href_lower and href_lower.endswith(".css"):
            technologies.append(
                Technology(
                    name="Bootstrap",
                    category="CSS Framework",
                    confidence="high",
                    detection_method="link_url",
                    evidence=[_evidence(page.url, "link_url_bootstrap", href, "link")],
                )
            )

        if "tailwindcss" in href_lower:
            technologies.append(
                Technology(
                    name="Tailwind CSS",
                    category="CSS Framework",
                    confidence="high",
                    detection_method="link_url",
                    evidence=[_evidence(page.url, "link_url_tailwindcss", href, "link")],
                )
            )

    return technologies


def _check_http_headers(page: ParsedPage, raw_page: RawPage) -> list[Technology]:
    """Check HTTP headers for technology fingerprints."""
    technologies: list[Technology] = []
    server = raw_page.headers.get("Server", "")
    if not server:
        return technologies

    server_lower = server.lower()

    if "nginx" in server_lower:
        technologies.append(
            Technology(
                name="nginx",
                category="Web Server",
                confidence="high",
                detection_method="http_header",
                evidence=[_evidence(page.url, "header_server_nginx", server, "header")],
            )
        )

    if "apache" in server_lower:
        technologies.append(
            Technology(
                name="Apache",
                category="Web Server",
                confidence="high",
                detection_method="http_header",
                evidence=[_evidence(page.url, "header_server_apache", server, "header")],
            )
        )

    if "microsoft-iis" in server_lower or server_lower == "iis":
        technologies.append(
            Technology(
                name="IIS",
                category="Web Server",
                confidence="high",
                detection_method="http_header",
                evidence=[_evidence(page.url, "header_server_iis", server, "header")],
            )
        )

    return technologies


def _check_dom_signatures(page: ParsedPage) -> list[Technology]:
    """Check DOM for technology signatures."""
    technologies: list[Technology] = []
    root = page.root

    # Next.js
    if root.find("div", {"id": "__next"}) is not None:
        technologies.append(
            Technology(
                name="Next.js",
                category="Framework",
                confidence="medium",
                detection_method="dom_signature",
                evidence=[_evidence(page.url, "dom_id___next", 'id="__next"', "dom")],
            )
        )

    # Nuxt
    if root.find("div", {"id": "__nuxt"}) is not None:
        technologies.append(
            Technology(
                name="Nuxt",
                category="Framework",
                confidence="medium",
                detection_method="dom_signature",
                evidence=[_evidence(page.url, "dom_id___nuxt", 'id="__nuxt"', "dom")],
            )
        )

    # Angular
    ng_app = _find_by_attribute(root, "ng-app")
    if ng_app is not None:
        technologies.append(
            Technology(
                name="Angular",
                category="Framework",
                confidence="medium",
                detection_method="dom_signature",
                evidence=[_evidence(page.url, "dom_ng_app", "ng-app", "dom")],
            )
        )

    return technologies


def detect(raw_site: RawSite, parsed_site: ParsedSite) -> TechnologyResult:
    """Detect technologies from a RawSite and ParsedSite.

    Detection is deterministic and evidence-driven. Technologies are only
    reported when explicit evidence is found. No inference or guessing is
    performed.

    Args:
        raw_site: Raw site output from the scanner.
        parsed_site: Parsed site output from the HTML parser.

    Returns:
        TechnologyResult with per-page detected technologies.
    """
    pages: list[TechnologyPageResult] = []
    raw_page_map: dict[str, RawPage] = {p.url: p for p in raw_site.pages}

    for parsed_page in parsed_site.pages:
        raw_page = raw_page_map.get(parsed_page.url)
        technologies: list[Technology] = []

        technologies.extend(_check_meta_generator(parsed_page))
        technologies.extend(_check_script_urls(parsed_page))
        technologies.extend(_check_link_urls(parsed_page))
        if raw_page is not None:
            technologies.extend(_check_http_headers(parsed_page, raw_page))
        technologies.extend(_check_dom_signatures(parsed_page))

        deduplicated = _deduplicate(technologies)
        pages.append(TechnologyPageResult(url=parsed_page.url, technologies=deduplicated))

    return TechnologyResult(target_url=parsed_site.target_url, pages=pages)
