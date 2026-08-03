"""Unit tests for the Request Handler interface."""

from unittest.mock import MagicMock, patch

from aifme_scout.engine.request_handler import handle
from aifme_scout.utils.models import ScanRequest, ScanResult


def test_handle_signature_matches_architecture() -> None:
    from typing import get_type_hints

    hints = get_type_hints(handle)
    assert "return" in hints


@patch("aifme_scout.engine.request_handler.scan")
@patch("aifme_scout.engine.request_handler.parse")
@patch("aifme_scout.engine.request_handler.analyze")
@patch("aifme_scout.engine.request_handler.extract_metadata")
@patch("aifme_scout.engine.request_handler.detect_technology")
@patch("aifme_scout.engine.request_handler.extract_content")
@patch("aifme_scout.engine.request_handler.discover_social")
@patch("aifme_scout.engine.request_handler.resolve_competitors")
@patch("aifme_scout.engine.request_handler.collect_evidence")
@patch("aifme_scout.engine.request_handler.build_schema")
@patch("aifme_scout.engine.request_handler.summarize")
def test_handle_returns_scan_result(
    mock_summarize: MagicMock,
    mock_build_schema: MagicMock,
    mock_collect_evidence: MagicMock,
    mock_resolve_competitors: MagicMock,
    mock_discover_social: MagicMock,
    mock_extract_content: MagicMock,
    mock_detect_technology: MagicMock,
    mock_extract_metadata: MagicMock,
    mock_analyze: MagicMock,
    mock_parse: MagicMock,
    mock_scan: MagicMock,
) -> None:
    mock_raw_site = MagicMock()
    mock_raw_site.target_url = "https://example.com"
    mock_scan.return_value = mock_raw_site

    mock_parsed = MagicMock()
    mock_parse.return_value = mock_parsed

    mock_analyze.return_value = MagicMock()
    mock_extract_metadata.return_value = MagicMock()
    mock_detect_technology.return_value = MagicMock()
    mock_extract_content.return_value = MagicMock()
    mock_discover_social.return_value = MagicMock()
    mock_resolve_competitors.return_value = MagicMock()

    mock_evidence_collection = MagicMock()
    mock_collect_evidence.return_value = mock_evidence_collection

    from aifme_scout.extractors.models import (
        ScoutMeta,
        ScoutSchema,
        ScoutSite,
    )
    from aifme_scout.utils.models import Summary

    mock_schema = ScoutSchema(
        meta=ScoutMeta(
            schema_version="1.0.0",
            engine_version="1.0.0-rc2",
            timestamp="2024-01-01T00:00:00+00:00",
        ),
        site=ScoutSite(url="https://example.com", target_url="https://example.com"),
        seo=[],
        metadata=[],
        technology=[],
        content=[],
        social=[],
        competitors=[],
        evidence=[],
        diagnostics={
            "total_evidence_items": 0,
            "seo_items": 0,
            "metadata_items": 0,
            "technology_items": 0,
            "content_items": 0,
            "social_items": 0,
            "competitor_items": 0,
            "build_timestamp": "2024-01-01T00:00:00+00:00",
        },
    )
    mock_build_schema.return_value = mock_schema

    mock_summary = Summary(text="", evidence_refs=[])
    mock_summarize.return_value = mock_summary

    request = ScanRequest(target_url="https://example.com")
    result = handle(request)

    assert isinstance(result, ScanResult)
    assert result.meta.schema_version == "1.0.0"
    assert result.target.url == "https://example.com"
    assert result.summary == mock_summary

