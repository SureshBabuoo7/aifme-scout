"""Unit tests for the Website Scanner module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aifme_scout.scanner.robots import is_path_allowed, parse_robots_txt
from aifme_scout.scanner.scanner import (
    MAX_RESPONSE_SIZE_BYTES,
    InvalidURLError,
    ResponseTooLargeError,
    RobotsDisallowedError,
    ScannerService,
    ScanOptions,
    UnsupportedContentTypeError,
)


class TestRobotsParser:
    def test_parse_empty(self) -> None:
        policy = parse_robots_txt("")
        assert policy.disallowed_paths == []
        assert policy.allowed_paths == []

    def test_parse_disallow(self) -> None:
        policy = parse_robots_txt("User-agent: *\nDisallow: /admin\n")
        assert "/admin" in policy.disallowed_paths

    def test_parse_allow(self) -> None:
        policy = parse_robots_txt("User-agent: *\nAllow: /public\n")
        assert "/public" in policy.allowed_paths

    def test_parse_crawl_delay(self) -> None:
        policy = parse_robots_txt("User-agent: *\nCrawl-delay: 2\n")
        assert policy.crawl_delay_ms == 2000

    def test_parse_specific_user_agent(self) -> None:
        content = "User-agent: Googlebot\nDisallow: /private\n\nUser-agent: *\nDisallow: /admin\n"
        policy = parse_robots_txt(content, user_agent="Googlebot")
        assert "/private" in policy.disallowed_paths
        assert "/admin" not in policy.disallowed_paths

    def test_parse_comments_ignored(self) -> None:
        content = "# This is a comment\nUser-agent: *\n# Another comment\nDisallow: /secret\n"
        policy = parse_robots_txt(content)
        assert "/secret" in policy.disallowed_paths


class TestRobotsPathCheck:
    def test_allowed_path(self) -> None:
        policy = parse_robots_txt("User-agent: *\nDisallow: /admin\n")
        assert is_path_allowed(policy, "/") is True
        assert is_path_allowed(policy, "/public") is True

    def test_disallowed_path(self) -> None:
        policy = parse_robots_txt("User-agent: *\nDisallow: /admin\n")
        assert is_path_allowed(policy, "/admin") is False
        assert is_path_allowed(policy, "/admin/dashboard") is False

    def test_empty_policy_allows_all(self) -> None:
        policy = parse_robots_txt("")
        assert is_path_allowed(policy, "/anything") is True


class TestSSRF:
    def test_https_url_allowed(self) -> None:
        from aifme_scout.scanner.ssrf import validate_target_url

        validate_target_url("https://example.com")

    def test_http_url_allowed(self) -> None:
        from aifme_scout.scanner.ssrf import validate_target_url

        validate_target_url("http://example.com")

    def test_invalid_scheme_raises(self) -> None:
        from aifme_scout.scanner.ssrf import validate_target_url

        with pytest.raises(InvalidURLError):
            validate_target_url("ftp://example.com")

    def test_localhost_raises(self) -> None:
        from aifme_scout.scanner.ssrf import validate_target_url

        with pytest.raises(InvalidURLError):
            validate_target_url("http://localhost/test")

    def test_private_ip_raises(self) -> None:
        from aifme_scout.scanner.ssrf import validate_target_url

        with pytest.raises(InvalidURLError):
            validate_target_url("http://192.168.1.1/test")


class TestScannerService:
    @pytest.mark.asyncio
    async def test_fetch_success(self) -> None:
        service = ScannerService()
        mock_page = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.final_url = "https://example.com"
        mock_page.status_code = 200
        mock_page.content_type = "text/html"
        mock_page.html = "<html><body>Hello</body></html>"
        mock_page.response_size_bytes = 25
        mock_page.response_time_ms = 100.0

        with (
            patch.object(service, "_resolve_robots_policy", return_value=None),
            patch(
                "aifme_scout.scanner.scanner.validate_target_url",
                return_value="https://example.com",
            ),
            patch(
                "aifme_scout.scanner.scanner.is_path_allowed",
                return_value=True,
            ),
            patch("aifme_scout.scanner.scanner.asyncio.sleep"),
            patch.object(service, "_fetch_page", return_value=mock_page) as mock_fetch,
        ):
            result = await service.scan("https://example.com")

        mock_fetch.assert_called_once()
        assert len(result.pages) == 1
        assert result.pages[0].status_code == 200
        assert result.pages[0].html == "<html><body>Hello</body></html>"

    @pytest.mark.asyncio
    async def test_fetch_redirect(self) -> None:
        service = ScannerService()
        mock_page = MagicMock()
        mock_page.url = "https://example.com/start"
        mock_page.final_url = "https://example.com/final"
        mock_page.status_code = 200

        with (
            patch.object(service, "_resolve_robots_policy", return_value=None),
            patch(
                "aifme_scout.scanner.scanner.validate_target_url",
                return_value="https://example.com/start",
            ),
            patch(
                "aifme_scout.scanner.scanner.is_path_allowed",
                return_value=True,
            ),
            patch("aifme_scout.scanner.scanner.asyncio.sleep"),
            patch.object(service, "_fetch_page", return_value=mock_page),
        ):
            result = await service.scan("https://example.com/start")

        assert result.pages[0].final_url == "https://example.com/final"

    @pytest.mark.asyncio
    async def test_robots_disallowed_raises(self) -> None:
        from aifme_scout.scanner.robots import RobotsPolicy

        policy = RobotsPolicy(user_agent="*", disallowed_paths=["/admin"])
        service = ScannerService()
        with (
            pytest.raises(RobotsDisallowedError),
            patch(
                "aifme_scout.scanner.scanner.validate_target_url",
                return_value="https://example.com/admin",
            ),
            patch.object(service, "_resolve_robots_policy", return_value=policy),
        ):
            await service.scan("https://example.com/admin")

    @pytest.mark.asyncio
    async def test_unsupported_content_type_raises(self) -> None:
        service = ScannerService()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"key": "value"}'
        mock_response.url = "https://example.com"
        mock_response.request.url = "https://example.com"
        mock_response.encoding = "utf-8"

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            pytest.raises(UnsupportedContentTypeError),
            patch.object(service, "_resolve_robots_policy", return_value=None),
            patch(
                "aifme_scout.scanner.scanner.validate_target_url",
                return_value="https://example.com",
            ),
            patch(
                "aifme_scout.scanner.scanner.is_path_allowed",
                return_value=True,
            ),
            patch("aifme_scout.scanner.scanner.asyncio.sleep"),
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            await service.scan("https://example.com")

    @pytest.mark.asyncio
    async def test_response_too_large_raises(self) -> None:
        service = ScannerService()
        options = ScanOptions(max_response_size_bytes=1000)
        large_html = "a" * (MAX_RESPONSE_SIZE_BYTES + 1)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = large_html
        mock_response.url = "https://example.com"
        mock_response.request.url = "https://example.com"
        mock_response.encoding = "utf-8"

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            pytest.raises(ResponseTooLargeError),
            patch.object(service, "_resolve_robots_policy", return_value=None),
            patch(
                "aifme_scout.scanner.scanner.validate_target_url",
                return_value="https://example.com",
            ),
            patch(
                "aifme_scout.scanner.scanner.is_path_allowed",
                return_value=True,
            ),
            patch("aifme_scout.scanner.scanner.asyncio.sleep"),
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            await service.scan("https://example.com", options)

    @pytest.mark.asyncio
    async def test_invalid_url_raises(self) -> None:
        service = ScannerService()
        with pytest.raises(InvalidURLError):
            await service.scan("not-a-url")
