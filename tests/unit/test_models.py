"""Unit tests for core data models."""

import pytest

from aifme_scout.utils.constants import ScanMode
from aifme_scout.utils.models import (
    SEO,
    Evidence,
    HealthStatus,
    Meta,
    Observation,
    ScanError,
    ScanOptions,
    ScanRequest,
    ScanResult,
    SocialProfile,
    Technology,
    Website,
)
from aifme_scout.utils.version import Version


def test_version_from_string() -> None:
    v = Version.from_string("1.2.3")
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3
    assert str(v) == "1.2.3"


def test_version_from_string_invalid() -> None:
    with pytest.raises(ValueError):
        Version.from_string("not-a-version")


def test_version_is_frozen() -> None:
    v = Version(1, 0, 0)
    with pytest.raises(AttributeError):
        v.major = 2  # type: ignore[misc]


def test_meta_default_timestamp() -> None:
    meta = Meta(schema_version="1.0.0", engine_version="1.0.0-rc2")
    assert meta.timestamp.endswith("Z")


def test_scan_request_defaults() -> None:
    req = ScanRequest(target_url="https://example.com")
    assert req.target_url == "https://example.com"
    assert req.competitor_urls == []
    assert req.mode == ScanMode.NO_LLM
    assert req.options.max_pages == 25


def test_scan_request_with_competitors() -> None:
    req = ScanRequest(
        target_url="https://example.com",
        competitor_urls=["https://competitor-a.com", "https://competitor-b.com"],
        mode=ScanMode.LLM,
    )
    assert len(req.competitor_urls) == 2
    assert req.mode == ScanMode.LLM


def test_scan_result_defaults() -> None:
    target = Website(url="https://example.com")
    meta = Meta(schema_version="1.0.0", engine_version="1.0.0-rc2")
    result = ScanResult(meta=meta, target=target)
    assert result.competitors == []
    assert result.evidence == []
    assert result.summary.text == ""
    assert result.observations == []
    assert result.errors == []


def test_website_defaults() -> None:
    site = Website(url="https://example.com")
    assert site.seo.has_title is False
    assert site.technology == []
    assert site.metadata.favicon_url is None
    assert site.content.headline is None
    assert site.social_profiles.profiles == []


def test_technology_model() -> None:
    tech = Technology(name="React", category="frontend", confidence="high")
    assert tech.name == "React"
    assert tech.category == "frontend"
    assert tech.confidence == "high"


def test_seo_model_defaults() -> None:
    seo = SEO()
    assert seo.has_title is False
    assert seo.has_canonical is False


def test_evidence_model() -> None:
    evidence = Evidence(claim="has title", source_url="https://example.com")
    assert evidence.confidence == "low"
    assert evidence.collected_at.endswith("Z")


def test_observation_model() -> None:
    obs = Observation(type="signal", description="test", evidence_ref="ev-1")
    assert obs.type == "signal"
    assert obs.evidence_ref == "ev-1"


def test_scan_error_model() -> None:
    err = ScanError(code="timeout", message="fetch timed out", target_url="https://example.com")
    assert err.code == "timeout"
    assert err.target_url == "https://example.com"


def test_health_status_defaults() -> None:
    status = HealthStatus()
    assert status.status == "ok"
    assert status.version == "1.0.0-rc2"


def test_social_profile_model() -> None:
    profile = SocialProfile(platform="twitter", url="https://twitter.com/example")
    assert profile.platform == "twitter"
    assert profile.url == "https://twitter.com/example"


def test_scan_options_defaults() -> None:
    opts = ScanOptions()
    assert opts.crawl_delay_ms == 1000
    assert opts.max_pages == 25
    assert opts.headless is False
