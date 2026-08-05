"""Unit tests for the Website Scanner module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aifme_scout.scanner.robots import is_path_allowed, parse_robots_txt
from aifme_scout.scanner.scanner import (
    MAX_RESPONSE_SIZE_BYTES,
    InvalidURLError,
    RateLimitedError,
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
            patch.object(service, "_fetch_page", return_value=(mock_page, None)) as mock_fetch,
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
            patch.object(service, "_fetch_page", return_value=(mock_page, None)),
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
    async def test_xml_text_xml_returns_limited_page(self) -> None:
        service = ScannerService()
        xml_body = '<?xml version="1.0"?><root><item>data</item></root>'
        mock_response = _mock_xml_response("https://example.com", "text/xml", xml_body)
        mock_client = _make_mock_client(mock_response)

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
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await service.scan("https://example.com")

        assert len(result.pages) == 1
        page = result.pages[0]
        assert page.is_xml is True
        assert page.xml_type == "generic-xml"
        assert page.content_type == "text/xml"
        assert page.html == xml_body

    @pytest.mark.asyncio
    async def test_xml_application_xml_returns_limited_page(self) -> None:
        service = ScannerService()
        xml_body = '<?xml version="1.0"?><data><entry>value</entry></data>'
        mock_response = _mock_xml_response("https://example.com", "application/xml", xml_body)
        mock_client = _make_mock_client(mock_response)

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
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await service.scan("https://example.com")

        assert len(result.pages) == 1
        assert result.pages[0].is_xml is True
        assert result.pages[0].xml_type == "generic-xml"

    @pytest.mark.asyncio
    async def test_xml_rss_classified_as_rss(self) -> None:
        service = ScannerService()
        rss_body = (
            '<?xml version="1.0"?>'
            "<rss version=\"2.0\">"
            "<channel><title>Feed</title></channel>"
            "</rss>"
        )
        mock_response = _mock_xml_response(
            "https://example.com/feed", "application/rss+xml", rss_body
        )
        mock_client = _make_mock_client(mock_response)

        with (
            patch.object(service, "_resolve_robots_policy", return_value=None),
            patch(
                "aifme_scout.scanner.scanner.validate_target_url",
                return_value="https://example.com/feed",
            ),
            patch(
                "aifme_scout.scanner.scanner.is_path_allowed",
                return_value=True,
            ),
            patch("aifme_scout.scanner.scanner.asyncio.sleep"),
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await service.scan("https://example.com/feed")

        assert len(result.pages) == 1
        assert result.pages[0].is_xml is True
        assert result.pages[0].xml_type == "rss"

    @pytest.mark.asyncio
    async def test_xml_atom_classified_as_atom(self) -> None:
        service = ScannerService()
        atom_body = (
            '<?xml version="1.0"?>'
            "<feed xmlns=\"http://www.w3.org/2005/Atom\">"
            "<title>Atom Feed</title>"
            "</feed>"
        )
        mock_response = _mock_xml_response(
            "https://example.com/atom", "application/atom+xml", atom_body
        )
        mock_client = _make_mock_client(mock_response)

        with (
            patch.object(service, "_resolve_robots_policy", return_value=None),
            patch(
                "aifme_scout.scanner.scanner.validate_target_url",
                return_value="https://example.com/atom",
            ),
            patch(
                "aifme_scout.scanner.scanner.is_path_allowed",
                return_value=True,
            ),
            patch("aifme_scout.scanner.scanner.asyncio.sleep"),
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await service.scan("https://example.com/atom")

        assert len(result.pages) == 1
        assert result.pages[0].is_xml is True
        assert result.pages[0].xml_type == "atom"

    @pytest.mark.asyncio
    async def test_xml_sitemap_extracts_page_urls(self) -> None:
        service = ScannerService()
        sitemap_body = (
            '<?xml version="1.0"?>'
            "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
            "<url><loc>https://example.com/page1</loc></url>"
            "<url><loc>https://example.com/page2</loc></url>"
            "</urlset>"
        )
        html_page1 = "<html><head><title>Page 1</title></head><body>Hello</body></html>"
        html_page2 = "<html><head><title>Page 2</title></head><body>World</body></html>"

        sitemap_response = _mock_xml_response(
            "https://example.com/sitemap.xml", "application/xml", sitemap_body
        )
        page1_response = _mock_html_response("https://example.com/page1", html_page1)
        page2_response = _mock_html_response("https://example.com/page2", html_page2)

        call_count = 0

        def _side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return sitemap_response
            if call_count == 2:
                return page1_response
            return page2_response

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=_side_effect)

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
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            result = await service.scan("https://example.com")

        assert len(result.pages) == 3
        assert result.pages[0].is_xml is True
        assert result.pages[0].xml_type == "sitemap"
        assert result.pages[1].html == html_page1
        assert result.pages[1].content_type == "text/html"
        assert result.pages[2].html == html_page2
        assert result.pages[2].content_type == "text/html"

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


def _mock_xml_response(url: str, content_type: str, body: str) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": content_type}
    response.text = body
    response.url = url
    response.request.url = url
    response.encoding = "utf-8"
    return response


def _mock_html_response(url: str, body: str) -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.headers = {"content-type": "text/html"}
    response.text = body
    response.url = url
    response.request.url = url
    response.encoding = "utf-8"
    return response


def _make_mock_client(response: MagicMock) -> MagicMock:
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.get = AsyncMock(return_value=response)
    return client


class TestSitemapURLs:
    def test_parse_robots_sitemap(self) -> None:
        content = "User-agent: *\nSitemap: https://example.com/sitemap.xml\n"
        policy = parse_robots_txt(content)
        assert len(policy.sitemap_urls) == 1
        assert policy.sitemap_urls[0] == "https://example.com/sitemap.xml"

    def test_parse_robots_multiple_sitemaps(self) -> None:
        content = (
            "User-agent: *\n"
            "Sitemap: https://example.com/sitemap1.xml\n"
            "Sitemap: https://example.com/sitemap2.xml\n"
        )
        policy = parse_robots_txt(content)
        assert len(policy.sitemap_urls) == 2
        assert "https://example.com/sitemap1.xml" in policy.sitemap_urls
        assert "https://example.com/sitemap2.xml" in policy.sitemap_urls


class TestAntiBotDetection:
    @pytest.mark.asyncio
    async def test_antibot_challenge_detected(self) -> None:
        service = ScannerService()
        html = "<html><body><h1>Checking your browser before accessing</h1></body></html>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = html
        mock_response.url = "https://example.com"
        mock_response.request.url = "https://example.com"
        mock_response.encoding = "utf-8"

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

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
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            page, _ = await service._fetch_page("https://example.com", ScanOptions())

        assert page.is_anti_bot_challenge is True

    @pytest.mark.asyncio
    async def test_normal_page_not_antibot(self) -> None:
        service = ScannerService()
        html = "<html><body><h1>Normal Page</h1></body></html>"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.text = html
        mock_response.url = "https://example.com"
        mock_response.request.url = "https://example.com"
        mock_response.encoding = "utf-8"

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

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
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            page, _ = await service._fetch_page("https://example.com", ScanOptions())

        assert page.is_anti_bot_challenge is False


class TestRateLimited:
    @pytest.mark.asyncio
    async def test_rate_limited_after_retries(self) -> None:
        service = ScannerService()
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.headers = {"content-type": "text/html", "retry-after": "1"}
        mock_429.text = ""
        mock_429.url = "https://example.com"
        mock_429.request.url = "https://example.com"
        mock_429.encoding = "utf-8"

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_429)

        with (
            patch("aifme_scout.scanner.scanner.asyncio.sleep"),
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
            pytest.raises(RateLimitedError),
        ):
            await service._fetch_page("https://example.com", ScanOptions())

    @pytest.mark.asyncio
    async def test_5xx_retried(self) -> None:
        service = ScannerService()
        call_count = 0

        def make_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.status_code = 500 if call_count == 1 else 200
            resp.headers = {"content-type": "text/html"}
            resp.text = "<html><body>OK</body></html>"
            resp.url = "https://example.com"
            resp.request.url = "https://example.com"
            resp.encoding = "utf-8"
            return resp

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=make_response)

        with (
            patch("aifme_scout.scanner.scanner.asyncio.sleep"),
            patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client),
        ):
            page, _ = await service._fetch_page("https://example.com", ScanOptions())

        assert page.status_code == 200
        assert call_count == 2


class TestFetchSitemapPages:
    @pytest.mark.asyncio
    async def test_fetch_sitemap_pages_success(self) -> None:
        service = ScannerService()
        sitemap_body = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://example.com/page1</loc></url>
    <url><loc>https://example.com/page2</loc></url>
</urlset>"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sitemap_body

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client):
            urls = await service._fetch_sitemap_pages(
                ["https://example.com/sitemap.xml"], ScanOptions()
            )

        assert len(urls) == 2
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls

    @pytest.mark.asyncio
    async def test_fetch_sitemap_pages_error(self) -> None:
        service = ScannerService()
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        with patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client):
            urls = await service._fetch_sitemap_pages(
                ["https://example.com/sitemap.xml"], ScanOptions()
            )

        assert urls == []

    @pytest.mark.asyncio
    async def test_fetch_sitemap_pages_max_limit(self) -> None:
        service = ScannerService()
        urls_xml = "\n".join(
            f"<url><loc>https://example.com/page{i}</loc></url>"
            for i in range(60)
        )
        sitemap_body = f'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls_xml}</urlset>'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sitemap_body

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("aifme_scout.scanner.scanner.httpx.AsyncClient", return_value=mock_client):
            urls = await service._fetch_sitemap_pages(
                ["https://example.com/sitemap.xml"], ScanOptions()
            )

        assert len(urls) <= 50
