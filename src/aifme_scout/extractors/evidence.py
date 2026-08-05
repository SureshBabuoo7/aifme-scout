"""Evidence Collector module.

Normalizes extractor outputs into a common evidence model.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from aifme_scout.extractors.models import (
    CompetitorProvenance,
    CompetitorResult,
    ContentElementProvenance,
    ContentResult,
    ElementProvenance,
    EvidenceCollection,
    EvidenceItem,
    EvidenceProvenance,
    MetadataResult,
    SEOResult,
    SocialProfileProvenance,
    SocialResult,
    TechnologyEvidence,
    TechnologyResult,
)
from aifme_scout.scanner.models import RawPage, RawSite

if TYPE_CHECKING:
    pass


def _utc_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(UTC).isoformat()


def _to_str(value: object) -> str:
    """Convert a value to a stable string representation."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list | tuple):
        return "|".join(_to_str(v) for v in value)
    if isinstance(value, dict):
        return "|".join(f"{k}={_to_str(v)}" for k, v in sorted(value.items()))
    return str(value)


def _make_id(
    evidence_type: str,
    extractor_source: str,
    page_url: str,
    value: object,
    provenance: EvidenceProvenance,
) -> str:
    """Create a deterministic evidence ID."""
    key = "|".join(
        [
            evidence_type,
            extractor_source,
            page_url,
            _to_str(value),
            provenance.page_url,
            provenance.dom_path or "",
            provenance.tag or "",
            provenance.attribute or "",
            provenance.original_text or "",
            provenance.original_url or "",
            provenance.detection_rule or "",
            provenance.source or "",
        ]
    )
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"ev-{digest}"


def _element_provenance_to_evidence(provenance: ElementProvenance | None) -> EvidenceProvenance:
    """Convert ElementProvenance to EvidenceProvenance."""
    if provenance is None:
        return EvidenceProvenance(page_url="")
    return EvidenceProvenance(
        page_url=provenance.page_url,
        tag=provenance.tag,
        attribute=provenance.attribute,
        original_text=provenance.text_snippet,
    )


def _content_provenance_to_evidence(
    provenance: ContentElementProvenance | None,
) -> EvidenceProvenance:
    """Convert ContentElementProvenance to EvidenceProvenance."""
    if provenance is None:
        return EvidenceProvenance(page_url="")
    attrs = provenance.attributes or {}
    attr_str = "|".join(f"{k}={v}" for k, v in sorted(attrs.items())) if attrs else None
    return EvidenceProvenance(
        page_url=provenance.page_url,
        dom_path=provenance.dom_path,
        tag=provenance.tag,
        attribute=attr_str,
        original_text=provenance.original_text,
    )


def _social_provenance_to_evidence(
    provenance: SocialProfileProvenance | None,
) -> EvidenceProvenance:
    """Convert SocialProfileProvenance to EvidenceProvenance."""
    if provenance is None:
        return EvidenceProvenance(page_url="")
    return EvidenceProvenance(
        page_url=provenance.page_url,
        dom_path=provenance.dom_path,
        tag=provenance.tag,
        attribute=provenance.attribute,
        original_url=provenance.original_url,
    )


def _competitor_provenance_to_evidence(
    provenance: CompetitorProvenance | None,
) -> EvidenceProvenance:
    """Convert CompetitorProvenance to EvidenceProvenance."""
    if provenance is None:
        return EvidenceProvenance(page_url="")
    return EvidenceProvenance(
        page_url=provenance.page_url,
        dom_path=provenance.dom_path,
        tag=provenance.tag,
        attribute=provenance.attribute,
        original_text=provenance.original_text,
        original_url=provenance.original_url,
    )


def _technology_evidence_to_provenance(evidence: TechnologyEvidence) -> EvidenceProvenance:
    """Convert TechnologyEvidence to EvidenceProvenance."""
    return EvidenceProvenance(
        page_url=evidence.page_url,
        detection_rule=evidence.detection_rule,
        original_text=evidence.matched_value,
        source=evidence.source,
    )


def _collect_seo_evidence(result: SEOResult | None) -> list[EvidenceItem]:
    """Collect evidence from SEO result."""
    if result is None:
        return []
    items: list[EvidenceItem] = []
    for page in result.pages:
        if page.title is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="SEO_TITLE",
                    extractor_source="seo",
                    value=page.title.value,
                    provenance=_element_provenance_to_evidence(page.title.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.meta_description is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="META_DESCRIPTION",
                    extractor_source="seo",
                    value=page.meta_description.value,
                    provenance=_element_provenance_to_evidence(page.meta_description.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.canonical is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CANONICAL",
                    extractor_source="seo",
                    value=page.canonical.value,
                    provenance=_element_provenance_to_evidence(page.canonical.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.robots is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="ROBOTS",
                    extractor_source="seo",
                    value=page.robots.value,
                    provenance=_element_provenance_to_evidence(page.robots.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.charset is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CHARSET",
                    extractor_source="seo",
                    value=page.charset,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.viewport is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="VIEWPORT",
                    extractor_source="seo",
                    value=page.viewport,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.language is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="LANGUAGE",
                    extractor_source="seo",
                    value=page.language,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.hreflang:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="HREFLANG",
                    extractor_source="seo",
                    value=page.hreflang,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.open_graph is not None and page.open_graph.title is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="OPEN_GRAPH",
                    extractor_source="seo",
                    value={
                        "title": page.open_graph.title,
                        "description": page.open_graph.description,
                        "url": page.open_graph.url,
                    },
                    provenance=_element_provenance_to_evidence(page.open_graph.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
            if page.open_graph.image is not None:
                items.append(
                    EvidenceItem(
                        evidence_id="",
                        evidence_type="OPEN_GRAPH_IMAGE",
                        extractor_source="seo",
                        value=page.open_graph.image,
                        provenance=EvidenceProvenance(page_url=page.url),
                        confidence="high",
                        page_url=page.url,
                        timestamp=_utc_timestamp(),
                    )
                )
            if page.open_graph.url is not None:
                items.append(
                    EvidenceItem(
                        evidence_id="",
                        evidence_type="OPEN_GRAPH_URL",
                        extractor_source="seo",
                        value=page.open_graph.url,
                        provenance=EvidenceProvenance(page_url=page.url),
                        confidence="high",
                        page_url=page.url,
                        timestamp=_utc_timestamp(),
                    )
                )
            if page.open_graph.type is not None:
                items.append(
                    EvidenceItem(
                        evidence_id="",
                        evidence_type="OPEN_GRAPH_TYPE",
                        extractor_source="seo",
                        value=page.open_graph.type,
                        provenance=EvidenceProvenance(page_url=page.url),
                        confidence="high",
                        page_url=page.url,
                        timestamp=_utc_timestamp(),
                    )
                )
            if page.open_graph.site_name is not None:
                items.append(
                    EvidenceItem(
                        evidence_id="",
                        evidence_type="OPEN_GRAPH_SITE_NAME",
                        extractor_source="seo",
                        value=page.open_graph.site_name,
                        provenance=EvidenceProvenance(page_url=page.url),
                        confidence="high",
                        page_url=page.url,
                        timestamp=_utc_timestamp(),
                    )
                )
        if page.twitter_card is not None and page.twitter_card.title is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="TWITTER_CARD",
                    extractor_source="seo",
                    value={
                        "title": page.twitter_card.title,
                        "description": page.twitter_card.description,
                    },
                    provenance=_element_provenance_to_evidence(page.twitter_card.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
            if page.twitter_card.card is not None:
                items.append(
                    EvidenceItem(
                        evidence_id="",
                        evidence_type="TWITTER_CARD_TYPE",
                        extractor_source="seo",
                        value=page.twitter_card.card,
                        provenance=EvidenceProvenance(page_url=page.url),
                        confidence="high",
                        page_url=page.url,
                        timestamp=_utc_timestamp(),
                    )
                )
            if page.twitter_card.image is not None:
                items.append(
                    EvidenceItem(
                        evidence_id="",
                        evidence_type="TWITTER_CARD_IMAGE",
                        extractor_source="seo",
                        value=page.twitter_card.image,
                        provenance=EvidenceProvenance(page_url=page.url),
                        confidence="high",
                        page_url=page.url,
                        timestamp=_utc_timestamp(),
                    )
                )
            if page.twitter_card.site is not None:
                items.append(
                    EvidenceItem(
                        evidence_id="",
                        evidence_type="TWITTER_CARD_SITE",
                        extractor_source="seo",
                        value=page.twitter_card.site,
                        provenance=EvidenceProvenance(page_url=page.url),
                        confidence="high",
                        page_url=page.url,
                        timestamp=_utc_timestamp(),
                    )
                )
        if page.pagination_rel:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="PAGINATION",
                    extractor_source="seo",
                    value=page.pagination_rel,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.has_amp:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="AMP_DETECTION",
                    extractor_source="seo",
                    value={"method": page.amp_detection_method} if page.amp_detection_method else True,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.schema_org_type is not None:
            value: object = page.schema_org_type
            if page.schema_org_name is not None:
                value = {"type": page.schema_org_type, "name": page.schema_org_name}
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="SCHEMA_ORG_TYPE",
                    extractor_source="seo",
                    value=value,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.structured_data is not None and page.structured_data.count > 0:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="STRUCTURED_DATA",
                    extractor_source="seo",
                    value={
                        "has_json_ld": page.structured_data.has_json_ld,
                        "has_microdata": page.structured_data.has_microdata,
                        "has_rdfa": page.structured_data.has_rdfa,
                    },
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.indexability is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="INDEXABILITY",
                    extractor_source="seo",
                    value={
                        "noindex": page.indexability.noindex,
                        "nofollow": page.indexability.nofollow,
                        "noarchive": page.indexability.noarchive,
                        "nosnippet": page.indexability.nosnippet,
                    },
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
    return items


def _collect_metadata_evidence(result: MetadataResult | None) -> list[EvidenceItem]:
    """Collect evidence from metadata result."""
    if result is None:
        return []
    items: list[EvidenceItem] = []
    for page in result.pages:
        if page.site_name is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="SITE_NAME",
                    extractor_source="metadata",
                    value=page.site_name.value,
                    provenance=_element_provenance_to_evidence(page.site_name.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.application_name is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="APPLICATION_NAME",
                    extractor_source="metadata",
                    value=page.application_name.value,
                    provenance=_element_provenance_to_evidence(page.application_name.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.generator is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="GENERATOR",
                    extractor_source="metadata",
                    value=page.generator.value,
                    provenance=_element_provenance_to_evidence(page.generator.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.author is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="AUTHOR",
                    extractor_source="metadata",
                    value=page.author.value,
                    provenance=_element_provenance_to_evidence(page.author.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.publisher is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="PUBLISHER",
                    extractor_source="metadata",
                    value=page.publisher.value,
                    provenance=_element_provenance_to_evidence(page.publisher.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.copyright is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="COPYRIGHT",
                    extractor_source="metadata",
                    value=page.copyright.value,
                    provenance=_element_provenance_to_evidence(page.copyright.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.theme_color is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="THEME_COLOR",
                    extractor_source="metadata",
                    value=page.theme_color.value,
                    provenance=_element_provenance_to_evidence(page.theme_color.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.color_scheme is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="COLOR_SCHEME",
                    extractor_source="metadata",
                    value=page.color_scheme.value,
                    provenance=_element_provenance_to_evidence(page.color_scheme.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for favicon in page.favicons:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="FAVICON",
                    extractor_source="metadata",
                    value=favicon.url,
                    provenance=_element_provenance_to_evidence(favicon.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for icon in page.apple_touch_icons:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="APPLE_TOUCH_ICON",
                    extractor_source="metadata",
                    value=icon.url,
                    provenance=_element_provenance_to_evidence(icon.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.manifest is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="MANIFEST",
                    extractor_source="metadata",
                    value=page.manifest.value,
                    provenance=_element_provenance_to_evidence(page.manifest.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for feed in page.rss_feeds:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="RSS_FEED",
                    extractor_source="metadata",
                    value=feed.url,
                    provenance=_element_provenance_to_evidence(feed.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for feed in page.atom_feeds:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="ATOM_FEED",
                    extractor_source="metadata",
                    value=feed.url,
                    provenance=_element_provenance_to_evidence(feed.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for link in page.alternate_links:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="ALTERNATE_LINK",
                    extractor_source="metadata",
                    value=link.url,
                    provenance=_element_provenance_to_evidence(link.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for tag in page.verification_tags:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="VERIFICATION_TAG",
                    extractor_source="metadata",
                    value={"platform": tag.platform, "value": tag.value},
                    provenance=_element_provenance_to_evidence(tag.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.web_app_capable:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="WEB_APP_CAPABLE",
                    extractor_source="metadata",
                    value=True,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.mobile_web_app_capable:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="MOBILE_WEB_APP_CAPABLE",
                    extractor_source="metadata",
                    value=True,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for hint in page.resource_hints:
            rel = hint.rel or ""
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type=rel.upper() if rel else "RESOURCE_HINT",
                    extractor_source="metadata",
                    value=hint.url,
                    provenance=_element_provenance_to_evidence(hint.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.csp is not None and page.csp.value is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_SECURITY_POLICY",
                    extractor_source="metadata",
                    value=page.csp.value,
                    provenance=_element_provenance_to_evidence(page.csp.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.msapplication_tile_image is not None and page.msapplication_tile_image.value is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="MSAPPLICATION_TILEIMAGE",
                    extractor_source="metadata",
                    value=page.msapplication_tile_image.value,
                    provenance=_element_provenance_to_evidence(page.msapplication_tile_image.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.msapplication_config is not None and page.msapplication_config.value is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="MSAPPLICATION_CONFIG",
                    extractor_source="metadata",
                    value=page.msapplication_config.value,
                    provenance=_element_provenance_to_evidence(page.msapplication_config.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.geo_meta:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="GEO_META",
                    extractor_source="metadata",
                    value=page.geo_meta,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
    return items


def _collect_technology_evidence(result: TechnologyResult | None) -> list[EvidenceItem]:
    """Collect evidence from technology result."""
    if result is None:
        return []
    items: list[EvidenceItem] = []
    for page in result.pages:
        for tech in page.technologies:
            for tech_evidence in tech.evidence:
                items.append(
                    EvidenceItem(
                        evidence_id="",
                        evidence_type="TECHNOLOGY",
                        extractor_source="technology",
                        value={
                            "name": tech.name,
                            "category": tech.category,
                            "version": tech.version,
                            "confidence": tech.confidence,
                            "detection_method": tech.detection_method,
                        },
                        provenance=_technology_evidence_to_provenance(tech_evidence),
                        confidence=tech.confidence,
                        page_url=page.url,
                        timestamp=_utc_timestamp(),
                    )
                )
    return items


def _collect_content_evidence(result: ContentResult | None) -> list[EvidenceItem]:
    """Collect evidence from content result."""
    if result is None:
        return []
    items: list[EvidenceItem] = []
    for page in result.pages:
        for heading in page.headings:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_HEADING",
                    extractor_source="content",
                    value={"level": heading.level, "text": heading.text},
                    provenance=_content_provenance_to_evidence(heading.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for paragraph in page.paragraphs:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_PARAGRAPH",
                    extractor_source="content",
                    value=paragraph.text,
                    provenance=_content_provenance_to_evidence(paragraph.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for content_list in page.lists:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_LIST",
                    extractor_source="content",
                    value={
                        "list_type": content_list.list_type,
                        "items": [item.text for item in content_list.items],
                    },
                    provenance=_content_provenance_to_evidence(content_list.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for table in page.tables:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_TABLE",
                    extractor_source="content",
                    value={"headers": table.headers, "rows": table.rows},
                    provenance=_content_provenance_to_evidence(table.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for image in page.images:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="IMAGE",
                    extractor_source="content",
                    value={"src": image.src, "alt": image.alt},
                    provenance=_content_provenance_to_evidence(image.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for link in page.links:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="LINK",
                    extractor_source="content",
                    value={"text": link.text, "href": link.href},
                    provenance=_content_provenance_to_evidence(link.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for button in page.buttons:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="BUTTON",
                    extractor_source="content",
                    value=button.text,
                    provenance=_content_provenance_to_evidence(button.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for form in page.forms:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="FORM",
                    extractor_source="content",
                    value={
                        "action": form.action,
                        "method": form.method,
                        "input_names": form.input_names,
                    },
                    provenance=_content_provenance_to_evidence(form.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for breadcrumb in page.breadcrumbs:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="BREADCRUMB",
                    extractor_source="content",
                    value=breadcrumb.items,
                    provenance=_content_provenance_to_evidence(breadcrumb.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.footer is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_FOOTER",
                    extractor_source="content",
                    value=page.footer.text,
                    provenance=_content_provenance_to_evidence(page.footer.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for email in page.contact_emails:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTACT_EMAIL",
                    extractor_source="content",
                    value=email,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for phone in page.contact_phones:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTACT_PHONE",
                    extractor_source="content",
                    value=phone,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for video in page.videos:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_VIDEO",
                    extractor_source="content",
                    value=video,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for audio in page.audios:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_AUDIO",
                    extractor_source="content",
                    value=audio,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for bq in page.blockquotes:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_BLOCKQUOTE",
                    extractor_source="content",
                    value=bq,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for code in page.code_blocks:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_CODE",
                    extractor_source="content",
                    value=code,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for dl in page.definition_lists:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_DEFINITION_LIST",
                    extractor_source="content",
                    value=dl,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.address is not None:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_ADDRESS",
                    extractor_source="content",
                    value=page.address,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        for fc in page.figure_captions:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="CONTENT_FIGURE_CAPTION",
                    extractor_source="content",
                    value=fc,
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
    return items


def _collect_social_evidence(result: SocialResult | None) -> list[EvidenceItem]:
    """Collect evidence from social result."""
    if result is None:
        return []
    items: list[EvidenceItem] = []
    for page in result.pages:
        for profile in page.profiles:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="SOCIAL_PROFILE",
                    extractor_source="social",
                    value={
                        "platform": profile.platform,
                        "url": profile.url,
                        "username": profile.username,
                        "detection_method": profile.detection_method,
                    },
                    provenance=_social_provenance_to_evidence(profile.provenance),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
    return items


def _collect_competitor_evidence(result: CompetitorResult | None) -> list[EvidenceItem]:
    """Collect evidence from competitor result."""
    if result is None:
        return []
    items: list[EvidenceItem] = []
    seen_ids: set[str] = set()
    for page in result.pages:
        for competitor in page.competitors:
            evidence = EvidenceItem(
                evidence_id="",
                evidence_type="COMPETITOR",
                extractor_source="competitors",
                value={
                    "name": competitor.name,
                    "url": competitor.url,
                    "discovery_method": competitor.discovery_method,
                },
                provenance=_competitor_provenance_to_evidence(competitor.provenance),
                confidence=competitor.confidence,
                page_url=page.url,
                timestamp=_utc_timestamp(),
            )
            items.append(evidence)
            seen_ids.add(competitor.url or competitor.name)
    for competitor in result.user_supplied:
        if competitor.url and competitor.url in seen_ids:
            continue
        items.append(
            EvidenceItem(
                evidence_id="",
                evidence_type="COMPETITOR",
                extractor_source="competitors",
                value={
                    "name": competitor.name,
                    "url": competitor.url,
                    "discovery_method": competitor.discovery_method,
                },
                provenance=_competitor_provenance_to_evidence(competitor.provenance),
                confidence=competitor.confidence,
                page_url=competitor.source,
                timestamp=_utc_timestamp(),
            )
        )
    return items


def _collect_scanner_evidence(raw_site: RawSite) -> list[EvidenceItem]:
    """Collect scanner-level evidence from RawSite."""
    items: list[EvidenceItem] = []
    target_url = raw_site.target_url

    for page in raw_site.pages:
        if page.is_anti_bot_challenge:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="ANTI_BOT_CHALLENGE",
                    extractor_source="scanner",
                    value="Anti-bot challenge detected (Cloudflare, Imperva, Datadome, or similar)",
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )
        if page.is_rate_limited:
            items.append(
                EvidenceItem(
                    evidence_id="",
                    evidence_type="RATE_LIMITED",
                    extractor_source="scanner",
                    value="Rate limited (429) after retries",
                    provenance=EvidenceProvenance(page_url=page.url),
                    confidence="high",
                    page_url=page.url,
                    timestamp=_utc_timestamp(),
                )
            )

    if raw_site.sitemap_pages_found > 0:
        items.append(
            EvidenceItem(
                evidence_id="",
                evidence_type="SITEMAP_DISCOVERED",
                extractor_source="scanner",
                value={"count": raw_site.sitemap_pages_found},
                provenance=EvidenceProvenance(page_url=target_url),
                confidence="high",
                page_url=target_url,
                timestamp=_utc_timestamp(),
            )
        )

    return items


def _sort_key(item: EvidenceItem) -> tuple[str, ...]:
    """Return a stable sort key for deterministic ordering."""
    return (
        item.evidence_type,
        item.extractor_source,
        item.page_url,
        _to_str(item.value),
        item.provenance.page_url,
        item.provenance.dom_path or "",
        item.provenance.tag or "",
        item.provenance.attribute or "",
        item.provenance.original_text or "",
        item.provenance.original_url or "",
        item.provenance.detection_rule or "",
        item.provenance.source or "",
    )


def _deduplicate(items: list[EvidenceItem]) -> list[EvidenceItem]:
    """Remove duplicate evidence items, preserving order."""
    seen: set[str] = set()
    unique: list[EvidenceItem] = []
    for item in items:
        key = "|".join(
            [
                item.evidence_type,
                item.extractor_source,
                item.page_url,
                _to_str(item.value),
                item.provenance.page_url,
                item.provenance.dom_path or "",
                item.provenance.tag or "",
                item.provenance.attribute or "",
                item.provenance.original_text or "",
                item.provenance.original_url or "",
                item.provenance.detection_rule or "",
                item.provenance.source or "",
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def collect(
    seo_result: SEOResult | None = None,
    metadata_result: MetadataResult | None = None,
    technology_result: TechnologyResult | None = None,
    content_result: ContentResult | None = None,
    social_result: SocialResult | None = None,
    competitor_result: CompetitorResult | None = None,
    target_url: str = "",
    raw_site: RawSite | None = None,
) -> EvidenceCollection:
    """Collect and normalize evidence from all extractor outputs.

    Discovery is deterministic and evidence-driven. All upstream extractor
    outputs are normalized into a common evidence format. Provenance and
    confidence from upstream extractors are preserved.

    Args:
        seo_result: SEO extraction result.
        metadata_result: Metadata extraction result.
        technology_result: Technology detection result.
        content_result: Content extraction result.
        social_result: Social discovery result.
        competitor_result: Competitor discovery result.
        target_url: Canonical target URL.
        raw_site: Optional RawSite for scanner-level evidence (anti-bot, rate limit, sitemap).

    Returns:
        EvidenceCollection with normalized evidence items.
    """
    items: list[EvidenceItem] = []
    items.extend(_collect_seo_evidence(seo_result))
    items.extend(_collect_metadata_evidence(metadata_result))
    items.extend(_collect_technology_evidence(technology_result))
    items.extend(_collect_content_evidence(content_result))
    items.extend(_collect_social_evidence(social_result))
    items.extend(_collect_competitor_evidence(competitor_result))

    if raw_site is not None:
        items.extend(_collect_scanner_evidence(raw_site))

    deduplicated = _deduplicate(items)
    deduplicated.sort(key=_sort_key)

    final_items: list[EvidenceItem] = []
    for index, item in enumerate(deduplicated, start=1):
        evidence_id = f"ev-{index:06d}"
        provenance = item.provenance
        final_items.append(
            EvidenceItem(
                evidence_id=evidence_id,
                evidence_type=item.evidence_type,
                extractor_source=item.extractor_source,
                value=item.value,
                provenance=provenance,
                confidence=item.confidence,
                page_url=item.page_url,
                timestamp=item.timestamp,
                attributes=dict(item.attributes),
            )
        )

    return EvidenceCollection(target_url=target_url, items=final_items)
