"""SSRF protection utilities."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class SSRFViolation(Exception):
    """Raised when a target URL violates SSRF protection policy."""


class InvalidURLError(SSRFViolation):
    """Raised when the target URL is invalid or unsupported."""


def _is_private_ip(ip_str: str) -> bool:
    """Check if an IP address is private, loopback, or link-local."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return bool(
            ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
        )
    except ValueError:
        return False


def validate_target_url(url: str, allow_private: bool = False) -> str:
    """Validate that a target URL is safe to fetch.

    Raises InvalidURLError if the URL is malformed or targets a private IP.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise InvalidURLError(f"Unsupported scheme: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise InvalidURLError("URL has no hostname")

    try:
        resolved_ips = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise InvalidURLError(f"Cannot resolve hostname: {hostname}") from exc

    for _family, _, _, _, sockaddr in resolved_ips:
        ip_str = str(sockaddr[0])
        if _is_private_ip(ip_str) and not allow_private:
            raise InvalidURLError(f"Target resolves to private/internal IP: {ip_str}")

    return url
