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
from aifme_scout.utils.constants import DEFAULT_CRAWL_DELAY_MS, DEFAULT_MAX_PAGES
from aifme_scout.utils.exceptions import ScoutError
from aifme_scout.utils.logging import get_logger
from aifme_scout.utils.models import ScanError as ModelScanError

MAX_REDIRECTS = 10
MAX_RESPONSE_SIZE_BYTES = 10 * 1024 * 1024
USER_AGENT = "AIFME-Scout-OSS/0.0.0"


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
    )


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

    def __init__(self, config: Configuration | None = None) -> None:
        self._config = config
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

        try:
            page = await self._fetch_page(validated_url, options)
            pages.append(page)
        except (UnsupportedContentTypeError, ResponseTooLargeError):
            raise
        except Exception as exc:
            self._logger.error("Fetch failed for %s: %s", validated_url, exc)
            errors.append(ModelScanError(code="fetch_error", message=str(exc), target_url=url))
            raise FetchError(str(exc)) from exc

        return RawSite(
            target_url=url,
            pages=pages,
            sitemap_urls=[],
            robots_policy=robots_policy,
            crawl_depth=0,
            errors=errors,
        )

    async def _fetch_page(self, url: str, options: ScanOptions) -> RawPage:
        """Fetch a single page and return transport metadata."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
        }

        start_time = time.perf_counter()
        async with httpx.AsyncClient(
            follow_redirects=options.follow_redirects,
            max_redirects=MAX_REDIRECTS,
            timeout=httpx.Timeout(options.timeout_seconds),
            headers=headers,
        ) as client:
            response = await client.get(url)

        response_time_ms = (time.perf_counter() - start_time) * 1000.0

        content_type = response.headers.get("content-type", "")
        if not any(ct in content_type for ct in options.allowed_content_types):
            raise UnsupportedContentTypeError(f"Unsupported content type: {content_type}")

        html = response.text
        response_size = len(html.encode("utf-8"))
        if response_size > options.max_response_size_bytes:
            raise ResponseTooLargeError(
                f"Response size {response_size} exceeds limit {options.max_response_size_bytes}"
            )

        encoding = response.encoding or "utf-8"

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
        )

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

    async def _enforce_crawl_delay(self, delay_ms: int) -> None:
        """Enforce crawl delay between requests."""
        now = asyncio.get_event_loop().time()
        elapsed_ms = (now - self._last_fetch_time) * 1000.0
        remaining_ms = delay_ms - elapsed_ms
        if remaining_ms > 0:
            await asyncio.sleep(remaining_ms / 1000.0)
        self._last_fetch_time = asyncio.get_event_loop().time()


def scan(url: str, options: ScanOptions | None = None) -> RawSite:
    """Synchronous wrapper for the scanner service."""
    service = ScannerService()
    return asyncio.run(service.scan(url, options))
