"""Metadata Extractor module.

Pulls structured metadata from the parsed head region.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aifme_scout.extractors.models import (
    ElementProvenance,
    MetadataPageResult,
    MetadataResult,
    MetaLink,
    MetaValue,
    VerificationTag,
)
from aifme_scout.parser.models import Element, ParsedSite

if TYPE_CHECKING:
    pass


def _meta_value(element: Element | None, attribute: str | None = None) -> MetaValue | None:
    if element is None:
        return None
    from aifme_scout.extractors.models import ElementProvenance

    value = element.get(attribute) if attribute else element.text.strip() or element.get("content")
    return MetaValue(
        value=value,
        provenance=ElementProvenance(
            page_url=element._parent.tag if element._parent else "",
            tag=element.tag,
            attribute=attribute,
            text_snippet=element.text[:200] if element.text else None,
        ),
    )


def _meta_link(
    element: Element | None, rel: str | None = None, type_: str | None = None
) -> MetaLink | None:
    if element is None:
        return None
    from aifme_scout.extractors.models import ElementProvenance

    href = element.get("href")
    if not href:
        return None
    return MetaLink(
        url=href,
        rel=rel or element.get("rel"),
        type_=type_ or element.get("type"),
        provenance=ElementProvenance(
            page_url=element._parent.tag if element._parent else "",
            tag=element.tag,
            attribute="href",
            text_snippet=href[:200],
        ),
    )


def _collect_links(head: Element | None, rel: str, type_: str | None = None) -> list[MetaLink]:
    if head is None:
        return []
    results: list[MetaLink] = []
    for link in head.find_all("link"):
        link_rel = link.get("rel")
        if link_rel and rel in link_rel.split():
            meta_link = _meta_link(link, rel=rel, type_=type_)
            if meta_link is not None:
                results.append(meta_link)
    return results


def _collect_verification_tags(head: Element | None) -> list[VerificationTag]:
    if head is None:
        return []
    tags: list[VerificationTag] = []
    for meta in head.find_all("meta"):
        name = meta.get("name", "")
        content = meta.get("content", "")
        if not content:
            continue
        if name == "google-site-verification":
            from aifme_scout.extractors.models import ElementProvenance

            tags.append(
                VerificationTag(
                    platform="google",
                    value=content,
                    provenance=ElementProvenance(
                        page_url=meta._parent.tag if meta._parent else "",
                        tag=meta.tag,
                        attribute="content",
                        text_snippet=content[:200],
                    ),
                )
            )
        elif name == "msvalidate.01":
            from aifme_scout.extractors.models import ElementProvenance

            tags.append(
                VerificationTag(
                    platform="bing",
                    value=content,
                    provenance=ElementProvenance(
                        page_url=meta._parent.tag if meta._parent else "",
                        tag=meta.tag,
                        attribute="content",
                        text_snippet=content[:200],
                    ),
                )
            )
        elif name == "yandex-verification":
            from aifme_scout.extractors.models import ElementProvenance

            tags.append(
                VerificationTag(
                    platform="yandex",
                    value=content,
                    provenance=ElementProvenance(
                        page_url=meta._parent.tag if meta._parent else "",
                        tag=meta.tag,
                        attribute="content",
                        text_snippet=content[:200],
                    ),
                )
            )
        elif name == "facebook-domain-verification":
            from aifme_scout.extractors.models import ElementProvenance

            tags.append(
                VerificationTag(
                    platform="facebook",
                    value=content,
                    provenance=ElementProvenance(
                        page_url=meta._parent.tag if meta._parent else "",
                        tag=meta.tag,
                        attribute="content",
                        text_snippet=content[:200],
                    ),
                )
            )
    return tags


def extract(parsed_site: ParsedSite) -> MetadataResult:
    """Extract structured metadata from a ParsedSite.

    Args:
        parsed_site: Parsed site from the HTML Parser.

    Returns:
        MetadataResult with per-page metadata.
    """
    pages: list[MetadataPageResult] = []

    for parsed_page in parsed_site.pages:
        head = parsed_page.head

        site_name = None
        application_name = None
        generator = None
        author = None
        publisher = None
        copyright = None
        theme_color = None
        color_scheme = None
        manifest = None
        web_app_capable = False
        mobile_web_app_capable = False
        csp = None
        msapplication_tile_image = None
        msapplication_config = None
        geo_meta: dict[str, str] = {}
        resource_hints: list[MetaLink] = []

        if head is not None:
            for meta in head.find_all("meta"):
                name = meta.get("name", "")
                content = meta.get("content", "")

                if name == "application-name":
                    application_name = _meta_value(meta, "content")
                    if site_name is None:
                        site_name = application_name
                elif name == "generator":
                    generator = _meta_value(meta, "content")
                elif name == "author":
                    author = _meta_value(meta, "content")
                elif name == "publisher":
                    publisher = _meta_value(meta, "content")
                elif name == "copyright":
                    copyright = _meta_value(meta, "content")
                elif name == "theme-color":
                    theme_color = _meta_value(meta, "content")
                elif name == "color-scheme":
                    color_scheme = _meta_value(meta, "content")
                elif name == "mobile-web-app-capable":
                    mobile_web_app_capable = (content or "").lower() == "yes"
                elif name == "apple-mobile-web-app-capable":
                    web_app_capable = (content or "").lower() == "yes"
                elif name == "content-security-policy":
                    csp = _meta_value(meta, "content")
                elif name == "msapplication-TileImage":
                    msapplication_tile_image = _meta_value(meta, "content")
                elif name == "msapplication-config":
                    msapplication_config = _meta_value(meta, "content")
                elif name.lower().startswith("geo."):
                    geo_meta[name] = content or ""

            og_site_name = head.find("meta", {"property": "og:site_name"})
            if og_site_name is not None and site_name is None:
                site_name = _meta_value(og_site_name, "content")

            manifest_link = head.find("link", {"rel": "manifest"})
            manifest = _meta_value(manifest_link, "href") if manifest_link is not None else None

            for link in head.find_all("link"):
                rel = link.get("rel", "")
                if rel:
                    rel_parts = rel.split() if isinstance(rel, str) else rel
                    if any(r in rel_parts for r in ("dns-prefetch", "preconnect", "prefetch", "preload")):
                        href = link.get("href", "")
                        if href:
                            resource_hints.append(
                                MetaLink(
                                    url=href,
                                    rel=rel,
                                    type_=link.get("type"),
                                    provenance=ElementProvenance(
                                        page_url=parsed_page.url,
                                        tag=link.tag,
                                        attribute="href",
                                        text_snippet=href[:200],
                                    ),
                                )
                            )

        favicons = _collect_links(head, "icon")
        apple_touch_icons = _collect_links(head, "apple-touch-icon")
        rss_feeds = _collect_links(head, "alternate", "application/rss+xml")
        atom_feeds = _collect_links(head, "alternate", "application/atom+xml")
        alternate_links = _collect_links(head, "alternate")
        verification_tags = _collect_verification_tags(head)

        pages.append(
            MetadataPageResult(
                url=parsed_page.url,
                site_name=site_name,
                application_name=application_name,
                generator=generator,
                author=author,
                publisher=publisher,
                copyright=copyright,
                theme_color=theme_color,
                color_scheme=color_scheme,
                favicons=favicons,
                apple_touch_icons=apple_touch_icons,
                manifest=manifest,
                rss_feeds=rss_feeds,
                atom_feeds=atom_feeds,
                alternate_links=alternate_links,
                verification_tags=verification_tags,
                web_app_capable=web_app_capable,
                mobile_web_app_capable=mobile_web_app_capable,
                csp=csp,
                msapplication_tile_image=msapplication_tile_image,
                msapplication_config=msapplication_config,
                geo_meta=geo_meta,
                resource_hints=resource_hints,
            )
        )

    return MetadataResult(target_url=parsed_site.target_url, pages=pages)
