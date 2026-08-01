"""Unit tests for the Social Discovery module."""

from pathlib import Path

from aifme_scout.extractors import SocialResult, discover_social
from aifme_scout.parser import parse
from aifme_scout.scanner.models import RawPage, RawSite


def _load_fixture(name: str) -> str:
    return Path("tests/fixtures/html").joinpath(name).read_text(encoding="utf-8")


def _make_raw_site(html: str, url: str = "https://example.com") -> RawSite:
    page = RawPage(
        url=url,
        final_url=url,
        status_code=200,
        headers={"content-type": "text/html"},
        html=html,
    )
    return RawSite(target_url=url, pages=[page], sitemap_urls=[])


def _parse(html: str, url: str = "https://example.com") -> SocialResult:
    raw_site = _make_raw_site(html, url)
    parsed = parse(raw_site)
    return discover_social(parsed)


def _get_profiles(result: SocialResult, url: str | None = None) -> list:
    if url is None:
        return result.pages[0].profiles
    for page in result.pages:
        if page.url == url:
            return page.profiles
    return []


def _platforms(profiles: list) -> set[str]:
    return {p.platform for p in profiles}


class TestPlatformDetection:
    def test_linkedin_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "LinkedIn" in _platforms(_get_profiles(result))

    def test_x_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "X" in _platforms(_get_profiles(result))

    def test_github_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "GitHub" in _platforms(_get_profiles(result))

    def test_youtube_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "YouTube" in _platforms(_get_profiles(result))

    def test_instagram_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "Instagram" in _platforms(_get_profiles(result))

    def test_facebook_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "Facebook" in _platforms(_get_profiles(result))

    def test_tiktok_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "TikTok" in _platforms(_get_profiles(result))

    def test_gitlab_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "GitLab" in _platforms(_get_profiles(result))

    def test_discord_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "Discord" in _platforms(_get_profiles(result))

    def test_reddit_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "Reddit" in _platforms(_get_profiles(result))

    def test_pinterest_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "Pinterest" in _platforms(_get_profiles(result))

    def test_threads_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "Threads" in _platforms(_get_profiles(result))

    def test_medium_detected(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        assert "Medium" in _platforms(_get_profiles(result))


class TestRelativeLinks:
    def test_relative_link_ignored(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        profiles = _get_profiles(result)
        assert not any(p.url.startswith("/") for p in profiles)

    def test_absolute_url_returned(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        profiles = _get_profiles(result)
        github = next(p for p in profiles if p.platform == "GitHub")
        assert github.url == "https://github.com/aifme/scout"


class TestDuplicateLinks:
    def test_duplicate_links_eliminated(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        profiles = _get_profiles(result)
        linkedin = [p for p in profiles if p.platform == "LinkedIn"]
        assert len(linkedin) == 1
        assert linkedin[0].url == "https://linkedin.com/company/aifme"


class TestInvalidLinks:
    def test_invalid_link_ignored(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        profiles = _get_profiles(result)
        assert not any("invalid-url" in p.url for p in profiles)


class TestUnknownPlatform:
    def test_unknown_platform_ignored(self) -> None:
        html = '<html><body><a href="https://unknown.example.com">Unknown</a></body></html>'
        result = _parse(html)
        assert _get_profiles(result) == []


class TestProvenance:
    def test_provenance_preserved(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        profiles = _get_profiles(result)
        assert len(profiles) > 0
        profile = profiles[0]
        assert profile.provenance is not None
        assert profile.provenance.page_url == "https://example.com"
        assert profile.provenance.tag == "a"
        assert profile.provenance.attribute == "href"

    def test_dom_path_preserved(self) -> None:
        html = _load_fixture("social-tech.html")
        result = _parse(html)
        profiles = _get_profiles(result)
        assert len(profiles) > 0
        assert profiles[0].provenance.dom_path.startswith("//")


class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        html = _load_fixture("social-tech.html")
        result1 = _parse(html)
        result2 = _parse(html)
        assert _platforms(_get_profiles(result1)) == _platforms(_get_profiles(result2))

    def test_multiple_pages_independent(self) -> None:
        raw_site = RawSite(
            target_url="https://example.com",
            pages=[
                RawPage(
                    url="https://example.com/",
                    final_url="https://example.com/",
                    status_code=200,
                    headers={"content-type": "text/html"},
                    html=_load_fixture("social-tech.html"),
                ),
                RawPage(
                    url="https://example.com/about",
                    final_url="https://example.com/about",
                    status_code=200,
                    headers={"content-type": "text/html"},
                    html=_load_fixture("minimal.html"),
                ),
            ],
            sitemap_urls=[],
        )
        parsed = parse(raw_site)
        result = discover_social(parsed)
        assert len(result.pages) == 2
        assert len(_get_profiles(result, "https://example.com/")) > 0
        assert _get_profiles(result, "https://example.com/about") == []


class TestEmptyPage:
    def test_empty_page_returns_empty_profiles(self) -> None:
        html = "<html><body></body></html>"
        result = _parse(html)
        assert _get_profiles(result) == []
