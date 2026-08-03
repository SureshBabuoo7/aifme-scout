"""Unit tests for the REST API module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from aifme_scout.api.app import app
from aifme_scout.scanner import (
    FetchError,
    InvalidURLError,
    ResponseTooLargeError,
    RobotsDisallowedError,
    SSRFViolationError,
    UnsupportedContentTypeError,
)
from aifme_scout.utils.exceptions import ConfigurationError
from aifme_scout.utils.models import ScanResult, Summary


def _make_scan_result() -> ScanResult:
    """Create a minimal ScanResult for testing."""
    from aifme_scout.utils.models import Meta, Website

    return ScanResult(
        meta=Meta(
            schema_version="1.0.0",
            engine_version="1.0.0-rc2",
            timestamp="2024-01-01T00:00:00+00:00",
        ),
        target=Website(url="https://example.com"),
        evidence=[],
        summary=Summary(text="", evidence_refs=[]),
        observations=[],
        errors=[],
    )


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_health_response_model(self) -> None:
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert "version" in data


class TestVersionEndpoint:
    """Tests for the /version endpoint."""

    def test_version_returns_200(self) -> None:
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data

    def test_version_matches_package_version(self) -> None:
        from aifme_scout import __version__

        response = client.get("/version")
        data = response.json()
        assert data["version"] == __version__


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_returns_200(self) -> None:
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "docs" in data
        assert "openapi" in data


class TestSuccessfulScan:
    """Tests for successful scan execution."""

    @patch("aifme_scout.api.app.handle")
    def test_scan_returns_200(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post("/scan", json={"url": "https://example.com"})
        assert response.status_code == 200

    @patch("aifme_scout.api.app.handle")
    def test_scan_returns_scan_result(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post("/scan", json={"url": "https://example.com"})
        data = response.json()
        assert "meta" in data
        assert "target" in data
        assert "evidence" in data
        assert "summary" in data

    @patch("aifme_scout.api.app.handle")
    def test_scan_with_mode_no_llm(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post("/scan", json={"url": "https://example.com", "mode": "no-llm"})
        assert response.status_code == 200

    @patch("aifme_scout.api.app.handle")
    def test_scan_with_mode_llm(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post("/scan", json={"url": "https://example.com", "mode": "llm"})
        assert response.status_code == 200

    @patch("aifme_scout.api.app.handle")
    def test_scan_with_custom_timeout(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post("/scan", json={"url": "https://example.com", "timeout": 30.0})
        assert response.status_code == 200

    @patch("aifme_scout.api.app.handle")
    def test_scan_with_custom_user_agent(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post(
            "/scan",
            json={"url": "https://example.com", "user_agent": "MyBot/1.0"},
        )
        assert response.status_code == 200


class TestInvalidRequest:
    """Tests for invalid request handling."""

    def test_scan_missing_url_returns_422(self) -> None:
        response = client.post("/scan", json={})
        assert response.status_code == 422

    def test_scan_invalid_mode_returns_422(self) -> None:
        response = client.post("/scan", json={"url": "https://example.com", "mode": "invalid"})
        assert response.status_code == 422

    def test_scan_invalid_output_returns_422(self) -> None:
        response = client.post("/scan", json={"url": "https://example.com", "output": "invalid"})
        assert response.status_code == 422

    def test_scan_empty_url_returns_422(self) -> None:
        response = client.post("/scan", json={"url": ""})
        assert response.status_code == 422


class TestErrorHandling:
    """Tests for error handling and HTTP status codes."""

    @patch("aifme_scout.api.app.handle")
    def test_invalid_url_returns_400(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = InvalidURLError("Invalid URL")
        response = client.post("/scan", json={"url": "not-a-url"})
        assert response.status_code == 400

    @patch("aifme_scout.api.app.handle")
    def test_network_failure_returns_408(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = FetchError("Network timeout")
        response = client.post("/scan", json={"url": "https://example.com"})
        assert response.status_code == 408

    @patch("aifme_scout.api.app.handle")
    def test_scanner_failure_returns_400(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = RobotsDisallowedError("robots.txt disallows")
        response = client.post("/scan", json={"url": "https://example.com"})
        assert response.status_code == 400

    @patch("aifme_scout.api.app.handle")
    def test_ssrf_failure_returns_400(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = SSRFViolationError("SSRF violation")
        response = client.post("/scan", json={"url": "https://example.com"})
        assert response.status_code == 400

    @patch("aifme_scout.api.app.handle")
    def test_response_too_large_returns_400(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = ResponseTooLargeError("Response too large")
        response = client.post("/scan", json={"url": "https://example.com"})
        assert response.status_code == 400

    @patch("aifme_scout.api.app.handle")
    def test_unsupported_content_type_returns_400(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = UnsupportedContentTypeError("Unsupported content type")
        response = client.post("/scan", json={"url": "https://example.com"})
        assert response.status_code == 400

    @patch("aifme_scout.api.app.handle")
    def test_configuration_error_returns_500(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = ConfigurationError("Invalid configuration")
        response = client.post("/scan", json={"url": "https://example.com"})
        assert response.status_code == 500

    @patch("aifme_scout.api.app.handle")
    def test_internal_error_returns_500(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = Exception("Unexpected error")
        response = client.post("/scan", json={"url": "https://example.com"})
        assert response.status_code == 500

    @patch("aifme_scout.api.app.handle")
    def test_error_response_does_not_expose_stack_trace(self, mock_handle: MagicMock) -> None:
        mock_handle.side_effect = Exception("Unexpected error")
        response = client.post("/scan", json={"url": "https://example.com"})
        data = response.json()
        assert "traceback" not in str(data).lower()
        assert "Traceback" not in str(data)


class TestOpenAPIGeneration:
    """Tests for OpenAPI schema generation."""

    def test_openapi_json_available(self) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_openapi_contains_scan_endpoint(self) -> None:
        response = client.get("/openapi.json")
        data = response.json()
        assert "/scan" in data["paths"]
        assert "post" in data["paths"]["/scan"]

    def test_openapi_contains_health_endpoint(self) -> None:
        response = client.get("/openapi.json")
        data = response.json()
        assert "/health" in data["paths"]
        assert "get" in data["paths"]["/health"]

    def test_openapi_contains_version_endpoint(self) -> None:
        response = client.get("/openapi.json")
        data = response.json()
        assert "/version" in data["paths"]
        assert "get" in data["paths"]["/version"]

    def test_docs_endpoint_available(self) -> None:
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint_available(self) -> None:
        response = client.get("/redoc")
        assert response.status_code == 200


class TestOutputFormats:
    """Tests for output format handling."""

    @patch("aifme_scout.api.app.handle")
    def test_scan_accepts_json_output(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post("/scan", json={"url": "https://example.com", "output": "json"})
        assert response.status_code == 200

    @patch("aifme_scout.api.app.handle")
    def test_scan_accepts_markdown_output(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post("/scan", json={"url": "https://example.com", "output": "markdown"})
        assert response.status_code == 200

    @patch("aifme_scout.api.app.handle")
    def test_scan_accepts_both_output(self, mock_handle: MagicMock) -> None:
        mock_handle.return_value = _make_scan_result()
        response = client.post("/scan", json={"url": "https://example.com", "output": "both"})
        assert response.status_code == 200
