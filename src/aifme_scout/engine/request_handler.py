"""Request Handler interface.

Defines the single entry point both the CLI and REST API call into.
"""

from __future__ import annotations

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
    Evidence,
    Meta,
    ScanError,
    ScanRequest,
    ScanResult,
    Summary,
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
    target = Website(url=schema.site.url)

    evidence = [
        Evidence(
            claim=str(item.value),
            source_url=item.page_url,
            confidence=item.confidence,
            collected_at=item.timestamp,
        )
        for item in schema.evidence
    ]

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
        target=target,
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
        user_agent=request.options.user_agent or "AIFME-Scout-OSS/1.0.0-rc1",
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
    )
    schema = build_schema(evidence_collection)
    summary = summarize(schema, mode=request.mode)

    return _map_schema_to_scan_result(schema, raw_site, summary)
