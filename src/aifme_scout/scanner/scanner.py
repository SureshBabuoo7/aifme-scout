"""Website Scanner module.

Fetches website resources safely and deterministically. Returns raw HTTP
responses and transport metadata only. No parsing, extraction, or
interpretation is performed at this layer.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from aifme_scout.scanner.models import RawPage, RawSite, RobotsPolicy
from aifme_scout.scanner.robots import is_path_allowed, parse_robots_txt
from aifme_scout.scanner.ssrf import InvalidURLError, validate_target_url
from aifme_scout.utils.config import Configuration
from aifme_scout.utils.constants import (
    ANTI_BOT_INDICATORS,
    DEFAULT_CRAWL_DELAY_MS,
    DEFAULT_MAX_PAGES,
    MAX_PAGES_PER_SITEMAP,
    MAX_SITEMAP_URLS,
    RETRY_BACKOFF_BASE_MS,
    RETRY_MAX_ATTEMPTS,
)
from aifme_scout.utils.exceptions import AntiBotChallengeError, RateLimitedError, ScoutError
from aifme_scout.utils.logging import get_logger
from aifme_scout.utils.models import ScanError as ModelScanError

MAX_REDIRECTS = 10
MAX_RESPONSE_SIZE_BYTES = 10 * 1024 * 1024
USER_AGENT = "AIFME-Scout-OSS/1.0.0-rc2"


class ScannerError(ScoutError):
    """Base exception for scanner errors."""


class FetchError(ScannerError):
    """Raised when an HTTP fetch fails."""


class SSRFViolationError(ScannerError):
    """Raised when SSRF protection blocks a request."""


class RobotsDisallowedError(ScannerError):
    """Raised when robots.txt disallows the target path."""


class ResponseTooLargeError(ScannerError):
    """Raised when the response exceeds the maximum size."""


class UnsupportedContentTypeError(ScannerError):
    """Raised when the content type is not supported."""


@dataclass(frozen=True)
class ScanOptions:
    """Options controlling a single scan run."""

    max_pages: int = DEFAULT_MAX_PAGES
    crawl_delay_ms: int = DEFAULT_CRAWL_DELAY_MS
    follow_redirects: bool = True
    timeout_seconds: float = 10.0
    max_response_size_bytes: int = MAX_RESPONSE_SIZE_BYTES
    allowed_content_types: tuple[str, ...] = (
        "text/html",
        "application/xhtml+xml",
        "text/plain",
        "application/xml",
        "text/xml",
        "application/rss+xml",
        "application/atom+xml",
    )


def _classify_xml(content_type: str, body: str) -> str | None:
    """Classify an XML response as sitemap, rss, atom, or generic-xml.

    Returns None when the response is not XML.
    """
    ct = (content_type or "").lower()
    xml_ct = any(
        token in ct
        for token in ("application/xml", "text/xml", "application/rss+xml", "application/atom+xml")
    )
    if not xml_ct:
        return None
    body_lower = (body or "").lower().strip()
    if body_lower.startswith("<?xml") and (
        "<urlset" in body_lower or "<sitemapindex" in body_lower
    ):
        return "sitemap"
    if "<rss" in body_lower:
        return "rss"
    if body_lower.startswith("<?xml") and ("<feed" in body_lower or "atom" in body_lower):
        return "atom"
    return "generic-xml"


def _extract_sitemap_urls(body: str) -> list[str]:
    """Extract page URLs from a sitemap XML body."""
    import re

    seen: set[str] = set()
    urls: list[str] = []
    for match in re.finditer(r"<loc[^>]*>([^<]+)</loc>", body, re.IGNORECASE):
        url = match.group(1).strip()
        if url and url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


class ScannerService:
    """HTTP fetch service for the Website Scanner module.

    Responsibilities:
    - HTTP GET request with configurable timeout
    - Safe redirect following
    - User-Agent header support
    - robots.txt awareness
    - HTTPS support
    - Response validation
    - Content-Type validation
    - Maximum response size protection
    - Response metadata collection
    - Raw HTML return
    - Structured error reporting
    """

    def __init__(
        self,
        config: Configuration | None = None,
        user_agent: str = USER_AGENT,
    ) -> None:
        self._config = config
        self._user_agent = user_agent
        self._logger = get_logger(__name__)
        self._last_fetch_time: float = 0.0

    async def scan(self, url: str, options: ScanOptions | None = None) -> RawSite:
        """Scan a single URL and return a RawSite.

        Args:
            url: The target URL to scan.
            options: Scan options. Uses defaults if not provided.

        Returns:
            RawSite with transport-level metadata.

        Raises:
            InvalidURLError: If the URL is malformed.
            SSRFViolationError: If SSRF protection blocks the request.
            RobotsDisallowedError: If robots.txt disallows the path.
            UnsupportedContentTypeError: If the response content type is not supported.
            ResponseTooLargeError: If the response exceeds the maximum size.
            FetchError: If the HTTP request fails.
        """
        if options is None:
            options = ScanOptions()

        errors: list[ModelScanError] = []
        pages: list[RawPage] = []

        try:
            validated_url = validate_target_url(url)
        except Exception as exc:
            raise InvalidURLError(str(exc)) from exc

        robots_policy = await self._resolve_robots_policy(validated_url)
        parsed = urlparse(validated_url)

        if robots_policy is not None and not is_path_allowed(robots_policy, parsed.path or "/"):
            raise RobotsDisallowedError(f"robots.txt disallows path: {parsed.path or '/'}")

        if robots_policy and robots_policy.crawl_delay_ms > 0:
            await self._enforce_crawl_delay(robots_policy.crawl_delay_ms)
        elif options.crawl_delay_ms > 0:
            await self._enforce_crawl_delay(options.crawl_delay_ms)

        sitemap_urls_from_xml: list[str] | None = None
        try:
            page, sitemap_urls_from_xml = await self._fetch_page(validated_url, options)
            pages.append(page)
        except (UnsupportedContentTypeError, ResponseTooLargeError):
            raise
        except AntiBotChallengeError as exc:
            self._logger.warning("Anti-bot challenge detected for %s: %s", validated_url, exc)
            errors.append(
                ModelScanError(
                    code="anti_bot_challenge", message=str(exc), target_url=url
                )
            )
            limited_page = RawPage(
                url=validated_url,
                final_url=validated_url,
                status_code=403,
                headers={},
                html="",
                content_type="text/html",
                encoding=None,
                response_size_bytes=0,
                response_time_ms=0.0,
                is_anti_bot_challenge=True,
            )
            pages.append(limited_page)
        except RateLimitedError as exc:
            self._logger.warning("Rate limited for %s: %s", validated_url, exc)
            errors.append(ModelScanError(code="rate_limited", message=str(exc), target_url=url))
            limited_page = RawPage(
                url=validated_url,
                final_url=validated_url,
                status_code=429,
                headers={},
                html="",
                content_type="text/html",
                encoding=None,
                response_size_bytes=0,
                response_time_ms=0.0,
                is_rate_limited=True,
            )
            pages.append(limited_page)
        except Exception as exc:
            self._logger.error("Fetch failed for %s: %s", validated_url, exc)
            errors.append(ModelScanError(code="fetch_error", message=str(exc), target_url=url))
            raise FetchError(str(exc)) from exc

        sitemap_pages_found = 0
        if robots_policy and robots_policy.sitemap_urls:
            sitemap_urls_to_fetch = robots_policy.sitemap_urls[:MAX_SITEMAP_URLS]
            remaining_slots = max(0, options.max_pages - len(pages))
            if remaining_slots > 0:
                sitemap_discovered = await self._fetch_sitemap_pages(sitemap_urls_to_fetch, options)
                sitemap_pages_found = len(sitemap_discovered)
                for sitemap_page_url in sitemap_discovered[:remaining_slots]:
                    try:
                        sitemap_page, _ = await self._fetch_page(sitemap_page_url, options)
                        pages.append(sitemap_page)
                    except ResponseTooLargeError:
                        raise
                    except Exception as exc:
                        self._logger.debug(
                            "Sitemap page fetch failed for %s: %s", sitemap_page_url, exc
                        )

        if sitemap_urls_from_xml:
            remaining_slots = max(0, options.max_pages - len(pages))
            for page_url in sitemap_urls_from_xml[:remaining_slots]:
                if page_url == validated_url:
                    continue
                try:
                    sitemap_page, _ = await self._fetch_page(page_url, options)
                    pages.append(sitemap_page)
                except ResponseTooLargeError:
                    raise
                except Exception as exc:
                    self._logger.debug(
                        "Sitemap page fetch failed for %s: %s", page_url, exc
                    )

        return RawSite(
            target_url=url,
            pages=pages,
            sitemap_urls=robots_policy.sitemap_urls if robots_policy else [],
            robots_policy=robots_policy,
            crawl_depth=0,
            errors=errors,
            sitemap_pages_found=sitemap_pages_found,
        )

    async def _fetch_page(self, url: str, options: ScanOptions) -> tuple[RawPage, list[str] | None]:
        """Fetch a single page and return transport metadata.

        Returns:
            A tuple of (RawPage, discovered_sitemap_urls|None).
            discovered_sitemap_urls is non-None only when the response is
            an XML sitemap and URLs were extracted from it.
        """
        headers = {
            "User-Agent": self._user_agent,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        timeout = httpx.Timeout(
            connect=5.0, read=options.timeout_seconds, write=5.0, pool=5.0
        )

        start_time = time.perf_counter()
        response = None
        last_exc = None

        for attempt in range(RETRY_MAX_ATTEMPTS):
            if attempt > 0:
                backoff_ms = RETRY_BACKOFF_BASE_MS * (2 ** (attempt - 1))
                await asyncio.sleep(backoff_ms / 1000.0)

            try:
                async with httpx.AsyncClient(
                    follow_redirects=options.follow_redirects,
                    max_redirects=MAX_REDIRECTS,
                    timeout=timeout,
                    headers=headers,
                ) as client:
                    response = await client.get(url)
            except Exception as exc:
                last_exc = exc
                error_message = str(exc)
                if "brotli" in error_message.lower() and (
                    "can_accept_more_data" in error_message.lower()
                ):
                    self._logger.warning(
                        "Brotli decompression failed for %s, retrying without Brotli", url
                    )
                    fallback_headers = dict(headers)
                    fallback_headers["Accept-Encoding"] = "gzip, deflate"
                    async with httpx.AsyncClient(
                        follow_redirects=options.follow_redirects,
                        max_redirects=MAX_REDIRECTS,
                        timeout=timeout,
                        headers=fallback_headers,
                    ) as client:
                        response = await client.get(url)
                        break
                continue

            if response is not None and response.status_code == 429:
                retry_after = response.headers.get("retry-after")
                wait_seconds = 1.0
                if retry_after is not None:
                    try:
                        wait_seconds = float(retry_after)
                    except (ValueError, TypeError):
                        wait_seconds = 1.0
                await asyncio.sleep(min(wait_seconds, 60.0))
                last_exc = RateLimitedError(
                    f"Rate limited (429) for {url} after retry"
                )
                continue

            if response is not None and 500 <= response.status_code < 600:
                last_exc = Exception(f"Server error {response.status_code} for {url}")
                continue

            break

        if response is None and last_exc is not None:
            raise last_exc

        if response is None:
            raise FetchError(f"Failed to fetch {url}")

        response_time_ms = (time.perf_counter() - start_time) * 1000.0

        if response.status_code == 429:
            raise RateLimitedError(f"Rate limited (429) for {url} after all retries")

        if 500 <= response.status_code < 600:
            raise FetchError(
                f"Server error {response.status_code} for {url} after all retries"
            )

        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in options.allowed_content_types):
            raise UnsupportedContentTypeError(f"Unsupported content type: {content_type}")

        html = response.text
        response_size = len(html.encode("utf-8"))
        if response_size > options.max_response_size_bytes:
            raise ResponseTooLargeError(
                f"Response size {response_size} exceeds limit {options.max_response_size_bytes}"
            )

        xml_type = _classify_xml(content_type, html)
        if xml_type is not None:
            sitemap_urls: list[str] | None = None
            if xml_type == "sitemap":
                sitemap_urls = _extract_sitemap_urls(html)
            xml_page = RawPage(
                url=str(response.request.url),
                final_url=str(response.url),
                status_code=response.status_code,
                headers=dict(response.headers),
                html=html,
                content_type=content_type,
                encoding=response.encoding or "utf-8",
                response_size_bytes=response_size,
                response_time_ms=response_time_ms,
                is_xml=True,
                xml_type=xml_type,
            )
            return xml_page, sitemap_urls

        encoding = response.encoding or "utf-8"
        content_encoding = response.headers.get("content-encoding")

        body_lower = html.lower() if html else ""
        is_anti_bot = any(indicator in body_lower for indicator in ANTI_BOT_INDICATORS)

        return RawPage(
            url=str(response.request.url),
            final_url=str(response.url),
            status_code=response.status_code,
            headers=dict(response.headers),
            html=html,
            content_type=content_type,
            encoding=encoding,
            response_size_bytes=response_size,
            response_time_ms=response_time_ms,
            content_encoding=content_encoding,
            is_anti_bot_challenge=is_anti_bot,
        ), None

    async def _resolve_robots_policy(self, base_url: str) -> RobotsPolicy | None:
        """Fetch and parse robots.txt for the given base URL."""
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=httpx.Timeout(5.0),
                headers={"User-Agent": USER_AGENT},
            ) as client:
                response = await client.get(robots_url)
                if response.status_code == 200:
                    return parse_robots_txt(response.text)
        except Exception:
            pass
        return None

    async def _fetch_sitemap_pages(
        self, sitemap_urls: list[str], options: ScanOptions
    ) -> list[str]:
        """Fetch sitemap URLs and extract page URLs.

        Args:
            sitemap_urls: List of sitemap URLs to fetch.
            options: Scan options.

        Returns:
            List of discovered page URLs (up to MAX_PAGES_PER_SITEMAP per sitemap).
        """
        import re

        discovered: list[str] = []
        seen: set[str] = set()

        for sitemap_url in sitemap_urls[:MAX_SITEMAP_URLS]:
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=httpx.Timeout(10.0),
                    headers={"User-Agent": USER_AGENT},
                ) as client:
                    response = await client.get(sitemap_url)
                    if response.status_code != 200:
                        continue
                    body = response.text
            except Exception:
                continue

            loc_pattern = re.compile(r"<loc[^>]*>([^<]+)</loc>", re.IGNORECASE)
            urls = loc_pattern.findall(body)
            for url in urls:
                url = url.strip()
                if url and url not in seen:
                    seen.add(url)
                    discovered.append(url)
                    if len(discovered) >= MAX_PAGES_PER_SITEMAP:
                        break
            if len(discovered) >= MAX_PAGES_PER_SITEMAP:
                break

        return discovered

    async def _enforce_crawl_delay(self, delay_ms: int) -> None:
        """Enforce crawl delay between requests."""
        now = asyncio.get_event_loop().time()
        elapsed_ms = (now - self._last_fetch_time) * 1000.0
        remaining_ms = delay_ms - elapsed_ms
        if remaining_ms > 0:
            await asyncio.sleep(remaining_ms / 1000.0)
        self._last_fetch_time = asyncio.get_event_loop().time()


def scan(
    url: str,
    options: ScanOptions | None = None,
    user_agent: str = USER_AGENT,
) -> RawSite:
    """Synchronous wrapper for the scanner service."""
    service = ScannerService(user_agent=user_agent)
    return asyncio.run(service.scan(url, options))
