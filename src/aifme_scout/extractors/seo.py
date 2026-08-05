"""SEO Extractor module.

Derives on-page SEO signals from a ParsedSite.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aifme_scout.extractors.models import (
    CanonicalURL,
    ElementProvenance,
    Heading,
    HeadingHierarchy,
    Indexability,
    MetaDescription,
    OpenGraphSEO,
    RobotsMeta,
    SEOPageResult,
    SEOResult,
    StructuredDataPresence,
    Title,
    TwitterCardSEO,
)
from aifme_scout.parser.models import Element, ParsedSite
from aifme_scout.utils.models import SEO

if TYPE_CHECKING:
    pass


def _provenance(element: Element, attribute: str | None = None) -> ElementProvenance:
    return ElementProvenance(
        page_url=element._parent.tag if element._parent else "",
        tag=element.tag,
        attribute=attribute,
        text_snippet=element.text[:200] if element.text else None,
    )


def _get_text(element: Element | None) -> str | None:
    if element is None:
        return None
    text = element.text.strip()
    return text if text else None


def _get_attr(element: Element | None, name: str) -> str | None:
    if element is None:
        return None
    return element.get(name)


def _collect_hreflang(head: Element | None) -> list[str]:
    if head is None:
        return []
    langs: list[str] = []
    for link in head.find_all("link"):
        rel = link.get("rel")
        if rel and "alternate" in rel.split():
            hreflang = link.get("hreflang")
            if hreflang:
                langs.append(hreflang)
    return sorted(langs)


def _check_structured_data(root: Element | None) -> StructuredDataPresence:
    if root is None:
        return StructuredDataPresence()
    has_json_ld = root.find("script", {"type": "application/ld+json"}) is not None
    has_microdata = (
        root.find("div", {"itemscope": "True"}) is not None
        or root.find("span", {"itemscope": "True"}) is not None
    )
    has_rdfa = any(
        root.find(tag, {"typeof": "True"}) is not None
        for tag in (
            "div",
            "span",
            "p",
            "article",
            "section",
            "header",
            "footer",
            "main",
            "aside",
            "nav",
            "figure",
        )
    )
    count = sum([has_json_ld, has_microdata, has_rdfa])
    return StructuredDataPresence(
        has_json_ld=has_json_ld, has_microdata=has_microdata, has_rdfa=has_rdfa, count=count
    )


def _extract_headings(body: Element | None) -> HeadingHierarchy:
    if body is None:
        return HeadingHierarchy()
    headings: list[Heading] = []
    for level in range(1, 7):
        tag = f"h{level}"
        for element in body.find_all(tag):
            headings.append(Heading(level=level, text=element.text.strip()))
    has_h1 = any(h.level == 1 for h in headings)
    h1_texts = [h.text for h in headings if h.level == 1]
    duplicate_h1_count = len(h1_texts) - len(set(h1_texts))
    valid = has_h1 and duplicate_h1_count == 0
    return HeadingHierarchy(
        headings=headings, valid=valid, has_h1=has_h1, duplicate_h1_count=duplicate_h1_count
    )


def _extract_indexability(head: Element | None) -> Indexability:
    if head is None:
        return Indexability()
    robots_meta = head.find("meta", {"name": "robots"})
    if robots_meta is None:
        return Indexability()
    content = robots_meta.get("content", "")
    if content is None:
        return Indexability()
    parts = {part.strip().lower() for part in content.split(",")}
    return Indexability(
        noindex="noindex" in parts,
        nofollow="nofollow" in parts,
        noarchive="noarchive" in parts,
        nosnippet="nosnippet" in parts,
    )


def analyze(parsed_site: ParsedSite) -> SEOResult:
    """Analyze a ParsedSite and return SEO signals.

    Args:
        parsed_site: Parsed site from the HTML Parser.

    Returns:
        SEOResult with per-page SEO signals.
    """
    pages: list[SEOPageResult] = []

    for parsed_page in parsed_site.pages:
        root = parsed_page.root
        head = parsed_page.head
        body = parsed_page.body

        title = None
        if head is not None:
            title_element = head.find("title")
            if title_element is not None:
                title = Title(value=_get_text(title_element))

        meta_description = None
        if head is not None:
            desc_element = head.find("meta", {"name": "description"})
            if desc_element is not None:
                meta_description = MetaDescription(value=desc_element.get("content"))

        canonical = None
        if head is not None:
            canonical_element = head.find("link", {"rel": "canonical"})
            if canonical_element is not None:
                href = canonical_element.get("href")
                canonical = CanonicalURL(value=href)

        robots = None
        if head is not None:
            robots_element = head.find("meta", {"name": "robots"})
            if robots_element is not None:
                robots = RobotsMeta(value=robots_element.get("content"))

        charset = None
        if head is not None:
            for meta in head.find_all("meta"):
                if meta.get("charset"):
                    charset = meta.get("charset")
                    break
            if charset is None:
                charset_meta = head.find("meta", {"http-equiv": "Content-Type"})
                if charset_meta is not None:
                    content = charset_meta.get("content", "")
                    if content and "charset=" in content:
                        charset = content.split("charset=")[-1].strip()

        viewport = None
        if head is not None:
            viewport_meta = head.find("meta", {"name": "viewport"})
            if viewport_meta is not None:
                viewport = viewport_meta.get("content")

        language = None
        if head is not None:
            html_element = root.find("html")
            if html_element is not None:
                language = html_element.get("lang")
            if language is None:
                lang_meta = head.find("meta", {"http-equiv": "Content-Language"})
                if lang_meta is not None:
                    language = lang_meta.get("content")

        heading_hierarchy = _extract_headings(body)
        hreflang = _collect_hreflang(head)

        open_graph = OpenGraphSEO()
        if head is not None:
            og_title = head.find("meta", {"property": "og:title"})
            if og_title is not None:
                open_graph = OpenGraphSEO(title=og_title.get("content"))
            og_desc = head.find("meta", {"property": "og:description"})
            if og_desc is not None:
                open_graph = OpenGraphSEO(
                    title=open_graph.title, description=og_desc.get("content")
                )
            og_url = head.find("meta", {"property": "og:url"})
            if og_url is not None:
                open_graph = OpenGraphSEO(
                    title=open_graph.title,
                    description=open_graph.description,
                    url=og_url.get("content"),
                )
            og_image = head.find("meta", {"property": "og:image"})
            if og_image is not None:
                open_graph = OpenGraphSEO(
                    title=open_graph.title,
                    description=open_graph.description,
                    url=open_graph.url,
                    image=og_image.get("content"),
                )
            og_type = head.find("meta", {"property": "og:type"})
            if og_type is not None:
                open_graph = OpenGraphSEO(
                    title=open_graph.title,
                    description=open_graph.description,
                    url=open_graph.url,
                    image=open_graph.image,
                    type=og_type.get("content"),
                )
            og_site_name = head.find("meta", {"property": "og:site_name"})
            if og_site_name is not None:
                open_graph = OpenGraphSEO(
                    title=open_graph.title,
                    description=open_graph.description,
                    url=open_graph.url,
                    image=open_graph.image,
                    type=open_graph.type,
                    site_name=og_site_name.get("content"),
                )

        twitter_card = TwitterCardSEO()
        if head is not None:
            tw_title = head.find("meta", {"name": "twitter:title"})
            if tw_title is not None:
                twitter_card = TwitterCardSEO(title=tw_title.get("content"))
            tw_desc = head.find("meta", {"name": "twitter:description"})
            if tw_desc is not None:
                twitter_card = TwitterCardSEO(
                    title=twitter_card.title, description=tw_desc.get("content")
                )
            tw_card = head.find("meta", {"name": "twitter:card"})
            if tw_card is not None:
                twitter_card = TwitterCardSEO(
                    title=twitter_card.title,
                    description=twitter_card.description,
                    card=tw_card.get("content"),
                )
            tw_image = head.find("meta", {"name": "twitter:image"})
            if tw_image is not None:
                twitter_card = TwitterCardSEO(
                    title=twitter_card.title,
                    description=twitter_card.description,
                    card=twitter_card.card,
                    image=tw_image.get("content"),
                )
            tw_site = head.find("meta", {"name": "twitter:site"})
            if tw_site is not None:
                twitter_card = TwitterCardSEO(
                    title=twitter_card.title,
                    description=twitter_card.description,
                    card=twitter_card.card,
                    image=twitter_card.image,
                    site=tw_site.get("content"),
                )

        structured_data = _check_structured_data(root)
        indexability = _extract_indexability(head)

        pagination_rel = []
        has_amp = False
        amp_detection_method = None
        schema_org_type = None
        schema_org_name = None

        if head is not None:
            for link in head.find_all("link"):
                rel = link.get("rel", "")
                if rel:
                    rel_parts = rel.split() if isinstance(rel, str) else rel
                    if "next" in rel_parts:
                        pagination_rel.append("next")
                    if "prev" in rel_parts:
                        pagination_rel.append("prev")
                    if "amphtml" in rel_parts:
                        has_amp = True
                        amp_detection_method = "link_rel"

        if root is not None:
            html_element = root.find("html")
            if html_element is not None and html_element.get("amp") is not None:
                has_amp = True
                amp_detection_method = "html_attribute"

            for script in root.find_all("script", {"type": "application/ld+json"}):
                import json
                import re as _re
                try:
                    raw = script.text or script.string or ""
                    raw = raw.strip()
                    if not raw:
                        continue
                    json_text = _re.sub(r'/\*.*?\*/', '', raw, flags=_re.DOTALL)
                    json_text = _re.sub(r'(?<!\S)//.*?$', '', json_text, flags=_re.MULTILINE)
                    data = json.loads(json_text)
                    if isinstance(data, dict):
                        s_type = data.get("@type") or data.get("type")
                        if s_type is None and "@graph" in data:
                            graph = data["@graph"]
                            if isinstance(graph, list):
                                for node in graph:
                                    if isinstance(node, dict):
                                        s_type = node.get("@type") or node.get("type")
                                        if s_type:
                                            break
                        if s_type:
                            schema_org_type = str(s_type)
                            schema_org_name = data.get("name")
                            break
                except Exception:
                    continue

        pages.append(
            SEOPageResult(
                url=parsed_page.url,
                title=title,
                meta_description=meta_description,
                canonical=canonical,
                robots=robots,
                hreflang=hreflang,
                charset=charset,
                viewport=viewport,
                language=language,
                heading_hierarchy=heading_hierarchy,
                open_graph=open_graph,
                twitter_card=twitter_card,
                structured_data=structured_data,
                indexability=indexability,
                pagination_rel=pagination_rel,
                has_amp=has_amp,
                amp_detection_method=amp_detection_method,
                schema_org_type=schema_org_type,
                schema_org_name=schema_org_name,
            )
        )

    return SEOResult(target_url=parsed_site.target_url, pages=pages)


def to_simple_seo(seo_result: SEOResult) -> SEO:
    """Convert SEOResult to the simple SEO dataclass.

    Args:
        seo_result: Detailed SEO extraction result.

    Returns:
        Simple SEO model.
    """
    pages = seo_result.pages
    if not pages:
        return SEO()
    first = pages[0]
    return SEO(
        has_title=first.title is not None and first.title.value is not None,
        has_meta_description=first.meta_description is not None
        and first.meta_description.value is not None,
        heading_structure_valid=first.heading_hierarchy.valid,
        has_canonical=first.canonical is not None and first.canonical.value is not None,
        has_sitemap=False,
        has_robots_txt=first.robots is not None and first.robots.value is not None,
    )
