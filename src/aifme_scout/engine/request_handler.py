"""Request Handler interface.

Defines the single entry point both the CLI and REST API call into.
"""

from __future__ import annotations

import json

from aifme_scout.engine.summary import summarize
from aifme_scout.extractors import (
    build_schema,
    collect_evidence,
    detect_technology,
    discover_social,
    extract_content,
    extract_metadata,
    resolve_competitors,
)
from aifme_scout.extractors.models import ScoutSchema
from aifme_scout.extractors.seo import analyze
from aifme_scout.parser import parse
from aifme_scout.scanner import scan
from aifme_scout.scanner.scanner import ScanOptions as ScannerScanOptions
from aifme_scout.utils.models import (
    Content,
    Evidence,
    Meta,
    Metadata,
    OpenGraph,
    ScanError,
    ScanRequest,
    ScanResult,
    SchemaOrg,
    SEO,
    SocialProfile,
    SocialProfiles,
    Summary,
    Technology,
    TwitterCard,
    Website,
)


def _map_schema_to_scan_result(
    schema: ScoutSchema,
    raw_site: object,
    summary: Summary,
) -> ScanResult:
    """Map internal pipeline outputs to the public ScanResult model."""
    meta = Meta(
        schema_version=schema.meta.schema_version,
        engine_version=schema.meta.engine_version,
        timestamp=schema.meta.timestamp,
    )

    evidence = [
        Evidence(
            claim=str(item.value),
            source_url=item.page_url,
            claim_type=item.evidence_type,
            confidence=item.confidence,
            collected_at=item.timestamp,
        )
        for item in schema.evidence
    ]

    tech_names: list[str] = []
    tech_categories: dict[str, str] = {}
    for item in schema.technology:
        if isinstance(item.value, dict):
            name = item.value.get("name")
            if isinstance(name, str):
                tech_names.append(name)
                category = item.value.get("category", "")
                if isinstance(category, str):
                    tech_categories[name] = category

    technologies = [
        Technology(name=name, category=tech_categories.get(name, ""))
        for name in tech_names
    ]

    social_profiles_list = []
    for item in schema.social:
        if isinstance(item.value, dict):
            platform = item.value.get("platform")
            url = item.value.get("url", "")
            if isinstance(platform, str) and platform not in {p.platform for p in social_profiles_list}:
                social_profiles_list.append(SocialProfile(platform=platform, url=url))

    seo_flags = {"has_title": False, "has_meta_description": False, "heading_structure_valid": False, "has_canonical": False, "has_sitemap": False, "has_robots_txt": False}
    for item in schema.seo:
        if item.evidence_type == "SEO_TITLE":
            seo_flags["has_title"] = True
        elif item.evidence_type == "META_DESCRIPTION":
            seo_flags["has_meta_description"] = True
        elif item.evidence_type == "CANONICAL":
            seo_flags["has_canonical"] = True
        elif item.evidence_type == "ROBOTS":
            seo_flags["has_robots_txt"] = True

    content_headline = None
    content_blocks: list[str] = []
    for item in schema.content:
        if item.evidence_type == "CONTENT_HEADING" and content_headline is None:
            if isinstance(item.value, str):
                content_headline = item.value
        if isinstance(item.value, str):
            content_blocks.append(item.value)
        elif isinstance(item.value, dict):
            for v in item.value.values():
                if isinstance(v, str):
                    content_blocks.append(v)

    content = Content(
        headline=content_headline,
        body_summary_blocks=content_blocks[:20],
        nav_labels=[],
    )

    social_profiles = SocialProfiles(profiles=social_profiles_list)

    og_title = og_desc = og_image = og_url = og_type = None
    tw_card = tw_title = tw_desc = tw_image = None
    schema_type = schema_name = None
    favicon_url = language = None
    for item in schema.metadata:
        if isinstance(item.value, dict):
            if item.evidence_type == "OPEN_GRAPH_TITLE":
                og_title = item.value.get("title")
            elif item.evidence_type == "OPEN_GRAPH_DESCRIPTION":
                og_desc = item.value.get("description")
            elif item.evidence_type == "OPEN_GRAPH_IMAGE":
                og_image = item.value.get("image")
            elif item.evidence_type == "FAVICON":
                favicon_url = item.value.get("url") if isinstance(item.value.get("url"), str) else None
        else:
            if item.evidence_type == "FAVICON_URL" and favicon_url is None:
                favicon_url = str(item.value) if item.value else None
            if item.evidence_type == "LANGUAGE" and language is None:
                language = str(item.value) if item.value else None

    og = OpenGraph(title=og_title, description=og_desc, image=og_image, url=og_url, type=og_type)
    tw = TwitterCard(card=tw_card, title=tw_title, description=tw_desc, image=tw_image)
    schema_org = SchemaOrg(type=schema_type, name=schema_name)
    metadata = Metadata(open_graph=og, twitter_card=tw, schema_org=schema_org, favicon_url=favicon_url, language=language)

    errors: list[ScanError] = []
    if hasattr(raw_site, "errors"):
        for err in raw_site.errors:
            errors.append(
                ScanError(
                    code=err.code,
                    message=err.message,
                    target_url=err.target_url,
                )
            )

    return ScanResult(
        meta=meta,
        target=Website(
            url=schema.site.url,
            seo=SEO(**seo_flags),
            technology=technologies,
            metadata=metadata,
            content=content,
            social_profiles=social_profiles,
        ),
        competitors=[],
        evidence=evidence,
        summary=summary,
        observations=[],
        errors=errors,
    )


def handle(request: ScanRequest) -> ScanResult:
    """Handle a scan request and return a ScanResult.

    This is the single entry point for both CLI and REST API invocations.
    It validates the request, resolves configuration, orchestrates the
    pipeline stage sequence, and assembles the final result.

    Args:
        request: The scan request containing target URL and options.

    Returns:
        ScanResult with the assembled scan output.

    Raises:
        ConfigurationError: If the configuration is invalid.
        ScoutError: If the scan fails.
    """
    scan_options = ScannerScanOptions(
        max_pages=request.options.max_pages,
        crawl_delay_ms=request.options.crawl_delay_ms,
        timeout_seconds=request.options.timeout or 10.0,
    )

    raw_site = scan(
        request.target_url,
        scan_options,
        user_agent=request.options.user_agent or "AIFME-Scout-OSS/1.0.0-rc2",
    )

    parsed = parse(raw_site)
    seo_result = analyze(parsed)
    metadata_result = extract_metadata(parsed)
    technology_result = detect_technology(raw_site, parsed)
    content_result = extract_content(parsed)
    social_result = discover_social(parsed)
    competitor_result = resolve_competitors(parsed)
    evidence_collection = collect_evidence(
        seo_result=seo_result,
        metadata_result=metadata_result,
        technology_result=technology_result,
        content_result=content_result,
        social_result=social_result,
        competitor_result=competitor_result,
        target_url=request.target_url,
        raw_site=raw_site,
    )
    schema = build_schema(evidence_collection)
    summary = summarize(schema, mode=request.mode)

    return _map_schema_to_scan_result(schema, raw_site, summary)
