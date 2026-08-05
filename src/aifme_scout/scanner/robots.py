"""Robots.txt parsing and enforcement."""

from __future__ import annotations

from contextlib import suppress
from typing import Any
from urllib.parse import urlparse

from aifme_scout.scanner.models import RobotsPolicy


class RobotsParseError(Exception):
    """Raised when robots.txt cannot be parsed."""


def parse_robots_txt(content: str, user_agent: str = "*") -> RobotsPolicy:
    """Parse robots.txt content and return policy for the given user agent.

    The parser handles the standard robots.txt format:
    - User-agent lines
    - Disallow lines
    - Allow lines
    - Crawl-delay lines
    - Sitemap lines

    Returns a RobotsPolicy with the most specific matching user-agent rules.
    If a specific section exists for the target agent, only that section's
    rules are returned. Otherwise the wildcard (*) section is used.
    """
    policy = RobotsPolicy(user_agent=user_agent)
    sections: list[tuple[list[str], dict[str, list[str]]]] = []

    current_agents: list[str] = []
    current_rules: dict[str, list[str]] = {
        "disallow": [],
        "allow": [],
        "crawl_delay": [],
    }
    sitemap_urls: list[str] = []

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if ":" not in line:
            continue

        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()

        if key == "user-agent":
            if current_agents:
                sections.append((current_agents, current_rules))
            current_agents = [v.strip().lower() for v in value.split(",")]
            current_rules = {"disallow": [], "allow": [], "crawl_delay": []}
        elif key == "disallow" and current_agents and value:
            current_rules["disallow"].append(value)
        elif key == "allow" and current_agents and value:
            current_rules["allow"].append(value)
        elif key == "crawl-delay" and current_agents:
            try:
                delay_seconds = float(value)
                current_rules["crawl_delay"].append(str(int(delay_seconds * 1000)))
            except ValueError:
                pass
        elif key == "sitemap" and value:
            sitemap_urls.append(value)

    if current_agents:
        sections.append((current_agents, current_rules))

    target_agents = [ua.lower() for ua in user_agent.split(",")]
    matched_section = None

    for agents, rules in sections:
        if any(agent in target_agents or agent == "*" for agent in agents) and "*" not in agents:
            matched_section = rules
            break

    if matched_section is None:
        for agents, rules in sections:
            if "*" in agents:
                matched_section = rules
                break

    if matched_section:
        policy.allowed_paths = matched_section.get("allow", [])
        policy.disallowed_paths = matched_section.get("disallow", [])
        if matched_section.get("crawl_delay"):
            with suppress(ValueError, IndexError):
                policy.crawl_delay_ms = int(matched_section["crawl_delay"][0])

    policy.sitemap_urls = sitemap_urls
    return policy


def is_path_allowed(policy: RobotsPolicy, path: str) -> bool:
    """Check if a path is allowed by the given robots policy.

    robots.txt matching uses prefix matching. The longest matching rule wins.
    """
    if not policy.disallowed_paths:
        return True

    best_allow_match = ""
    best_disallow_match = ""

    for allowed in policy.allowed_paths:
        if (path == allowed or path.startswith(allowed)) and len(allowed) > len(best_allow_match):
            best_allow_match = allowed

    for disallowed in policy.disallowed_paths:
        if (path == disallowed or path.startswith(disallowed)) and len(disallowed) > len(
            best_disallow_match
        ):
            best_disallow_match = disallowed

    return not best_disallow_match or len(best_disallow_match) < len(best_allow_match)


def fetch_robots_txt(base_url: str, client: Any) -> str | None:
    """Fetch robots.txt for the given base URL."""
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = client.get(
            robots_url,
            follow_redirects=True,
            timeout=10.0,
        )
        if response.status_code == 200:
            text = response.text
            if isinstance(text, str):
                return text
            return str(text)
    except Exception:
        pass
    return None
