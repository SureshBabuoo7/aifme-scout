"""Unit tests for the Metadata Extractor module."""

from pathlib import Path

from aifme_scout.extractors import MetadataResult, extract_metadata
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


def _parse(html: str, url: str = "https://example.com") -> MetadataResult:
    raw_site = _make_raw_site(html, url)
    parsed = parse(raw_site)
    return extract_metadata(parsed)


class TestApplicationName:
    def test_application_name_extracted(self) -> None:
        html = (
            '<html><head><meta name="application-name" content="MyApp"></head><body></body></html>'
        )
        result = _parse(html)
        assert result.pages[0].application_name is not None
        assert result.pages[0].application_name.value == "MyApp"

    def test_missing_application_name(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].application_name is None


class TestGenerator:
    def test_generator_extracted(self) -> None:
        html = (
            '<html><head><meta name="generator" content="WordPress 6.0"></head><body></body></html>'
        )
        result = _parse(html)
        assert result.pages[0].generator is not None
        assert result.pages[0].generator.value == "WordPress 6.0"

    def test_missing_generator(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].generator is None


class TestAuthor:
    def test_author_extracted(self) -> None:
        html = '<html><head><meta name="author" content="John Doe"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].author is not None
        assert result.pages[0].author.value == "John Doe"

    def test_missing_author(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].author is None


class TestPublisher:
    def test_publisher_extracted(self) -> None:
        html = '<html><head><meta name="publisher" content="Acme Inc"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].publisher is not None
        assert result.pages[0].publisher.value == "Acme Inc"

    def test_missing_publisher(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].publisher is None


class TestCopyright:
    def test_copyright_extracted(self) -> None:
        html = '<html><head><meta name="copyright" content="2024 Acme"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].copyright is not None
        assert result.pages[0].copyright.value == "2024 Acme"

    def test_missing_copyright(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].copyright is None


class TestThemeColor:
    def test_theme_color_extracted(self) -> None:
        html = '<html><head><meta name="theme-color" content="#ff0000"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].theme_color is not None
        assert result.pages[0].theme_color.value == "#ff0000"

    def test_missing_theme_color(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].theme_color is None


class TestColorScheme:
    def test_color_scheme_extracted(self) -> None:
        html = (
            '<html><head><meta name="color-scheme" content="dark light"></head><body></body></html>'
        )
        result = _parse(html)
        assert result.pages[0].color_scheme is not None
        assert result.pages[0].color_scheme.value == "dark light"

    def test_missing_color_scheme(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].color_scheme is None


class TestFavicons:
    def test_favicon_extracted(self) -> None:
        html = '<html><head><link rel="icon" href="/favicon.ico"></head><body></body></html>'
        result = _parse(html)
        assert len(result.pages[0].favicons) == 1
        assert result.pages[0].favicons[0].url == "/favicon.ico"

    def test_multiple_favicons(self) -> None:
        html = (
            "<html><head>"
            '<link rel="icon" href="/favicon.ico">'
            '<link rel="icon" href="/favicon-32x32.png" sizes="32x32">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert len(result.pages[0].favicons) == 2

    def test_missing_favicon(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].favicons == []


class TestAppleTouchIcon:
    def test_apple_touch_icon_extracted(self) -> None:
        html = (
            "<html><head>"
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert len(result.pages[0].apple_touch_icons) == 1
        assert result.pages[0].apple_touch_icons[0].url == "/apple-touch-icon.png"

    def test_missing_apple_touch_icon(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].apple_touch_icons == []


class TestManifest:
    def test_manifest_extracted(self) -> None:
        html = '<html><head><link rel="manifest" href="/manifest.json"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].manifest is not None
        assert result.pages[0].manifest.value == "/manifest.json"

    def test_missing_manifest(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].manifest is None


class TestFeeds:
    def test_rss_feed_extracted(self) -> None:
        html = (
            "<html><head>"
            '<link rel="alternate" type="application/rss+xml" title="RSS" href="/feed.rss">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert len(result.pages[0].rss_feeds) == 1
        assert result.pages[0].rss_feeds[0].url == "/feed.rss"

    def test_atom_feed_extracted(self) -> None:
        html = (
            "<html><head>"
            '<link rel="alternate" type="application/atom+xml" title="Atom" href="/feed.atom">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert len(result.pages[0].atom_feeds) == 1
        assert result.pages[0].atom_feeds[0].url == "/feed.atom"

    def test_missing_feeds(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].rss_feeds == []
        assert result.pages[0].atom_feeds == []


class TestAlternateLinks:
    def test_alternate_links_extracted(self) -> None:
        html = '<html><head><link rel="alternate" href="/fr/"></head><body></body></html>'
        result = _parse(html)
        assert len(result.pages[0].alternate_links) == 1
        assert result.pages[0].alternate_links[0].url == "/fr/"

    def test_missing_alternate_links(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].alternate_links == []


class TestVerificationTags:
    def test_google_verification_extracted(self) -> None:
        html = (
            "<html><head>"
            '<meta name="google-site-verification" content="abc123">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert len(result.pages[0].verification_tags) == 1
        assert result.pages[0].verification_tags[0].platform == "google"
        assert result.pages[0].verification_tags[0].value == "abc123"

    def test_bing_verification_extracted(self) -> None:
        html = (
            '<html><head><meta name="msvalidate.01" content="bing123"></head><body></body></html>'
        )
        result = _parse(html)
        assert len(result.pages[0].verification_tags) == 1
        assert result.pages[0].verification_tags[0].platform == "bing"

    def test_yandex_verification_extracted(self) -> None:
        html = (
            "<html><head>"
            '<meta name="yandex-verification" content="yandex123">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert len(result.pages[0].verification_tags) == 1
        assert result.pages[0].verification_tags[0].platform == "yandex"

    def test_facebook_verification_extracted(self) -> None:
        html = (
            "<html><head>"
            '<meta name="facebook-domain-verification" content="fb123">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert len(result.pages[0].verification_tags) == 1
        assert result.pages[0].verification_tags[0].platform == "facebook"

    def test_multiple_verification_tags(self) -> None:
        html = (
            "<html><head>"
            '<meta name="google-site-verification" content="google123">'
            '<meta name="msvalidate.01" content="bing123">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert len(result.pages[0].verification_tags) == 2
        platforms = {t.platform for t in result.pages[0].verification_tags}
        assert platforms == {"google", "bing"}

    def test_missing_verification_tags(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].verification_tags == []


class TestWebAppCapable:
    def test_web_app_capable_extracted(self) -> None:
        html = (
            "<html><head>"
            '<meta name="apple-mobile-web-app-capable" content="yes">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert result.pages[0].web_app_capable is True

    def test_mobile_web_app_capable_extracted(self) -> None:
        html = (
            "<html><head>"
            '<meta name="mobile-web-app-capable" content="yes">'
            "</head><body></body></html>"
        )
        result = _parse(html)
        assert result.pages[0].mobile_web_app_capable is True

    def test_web_app_capable_missing(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert result.pages[0].web_app_capable is False
        assert result.pages[0].mobile_web_app_capable is False


class TestProvenance:
    def test_provenance_preserved(self) -> None:
        html = '<html><head><meta name="generator" content="WordPress"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].generator is not None
        assert result.pages[0].generator.provenance is not None
        assert result.pages[0].generator.provenance.tag == "meta"
        assert result.pages[0].generator.provenance.attribute == "content"

    def test_link_provenance_preserved(self) -> None:
        html = '<html><head><link rel="manifest" href="/manifest.json"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].manifest is not None
        assert result.pages[0].manifest.provenance is not None
        assert result.pages[0].manifest.provenance.tag == "link"


class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        html = _load_fixture("wordpress.html")
        result1 = _parse(html)
        result2 = _parse(html)
        assert result1.pages[0].generator == result2.pages[0].generator
        assert result1.pages[0].favicons == result2.pages[0].favicons
        assert result1.pages[0].verification_tags == result2.pages[0].verification_tags


class TestMissingMetadata:
    def test_all_missing_returns_empty(self) -> None:
        html = "<html><head></head><body></body></html>"
        result = _parse(html)
        page = result.pages[0]
        assert page.generator is None
        assert page.author is None
        assert page.publisher is None
        assert page.copyright is None
        assert page.theme_color is None
        assert page.color_scheme is None
        assert page.favicons == []
        assert page.apple_touch_icons == []
        assert page.manifest is None
        assert page.rss_feeds == []
        assert page.atom_feeds == []
        assert page.alternate_links == []
        assert page.verification_tags == []
        assert page.web_app_capable is False
        assert page.mobile_web_app_capable is False


class TestResourceHints:
    def test_dns_prefetch_detected(self) -> None:
        html = '<html><head><link rel="dns-prefetch" href="//cdn.example.com"></head><body></body></html>'
        result = _parse(html)
        assert len(result.pages[0].resource_hints) == 1
        assert result.pages[0].resource_hints[0].url == "//cdn.example.com"

    def test_preconnect_detected(self) -> None:
        html = '<html><head><link rel="preconnect" href="https://fonts.example.com"></head><body></body></html>'
        result = _parse(html)
        assert len(result.pages[0].resource_hints) == 1

    def test_prefetch_detected(self) -> None:
        html = '<html><head><link rel="prefetch" href="/next-page.html"></head><body></body></html>'
        result = _parse(html)
        assert len(result.pages[0].resource_hints) == 1

    def test_preload_detected(self) -> None:
        html = '<html><head><link rel="preload" href="/font.woff2" as="font"></head><body></body></html>'
        result = _parse(html)
        assert len(result.pages[0].resource_hints) == 1


class TestCSP:
    def test_csp_detected(self) -> None:
        html = '<html><head><meta name="content-security-policy" content="default-src \'self\'"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].csp is not None
        assert "default-src" in result.pages[0].csp.value


class TestMsApplication:
    def test_msapplication_tile_image_detected(self) -> None:
        html = '<html><head><meta name="msapplication-TileImage" content="/tile.png"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].msapplication_tile_image is not None
        assert result.pages[0].msapplication_tile_image.value == "/tile.png"

    def test_msapplication_config_detected(self) -> None:
        html = '<html><head><meta name="msapplication-config" content="/browserconfig.xml"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].msapplication_config is not None
        assert result.pages[0].msapplication_config.value == "/browserconfig.xml"


class TestGeoMeta:
    def test_geo_meta_detected(self) -> None:
        html = '<html><head><meta name="geo.region" content="US-CA"><meta name="geo.placename" content="San Francisco"></head><body></body></html>'
        result = _parse(html)
        assert result.pages[0].geo_meta.get("geo.region") == "US-CA"
        assert result.pages[0].geo_meta.get("geo.placename") == "San Francisco"
