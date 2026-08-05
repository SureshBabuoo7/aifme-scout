"""Unit tests for the Technology Detector module."""

from pathlib import Path

from aifme_scout.extractors import TechnologyResult, detect_technology
from aifme_scout.parser import parse
from aifme_scout.scanner.models import RawPage, RawSite


def _load_fixture(name: str) -> str:
    return Path("tests/fixtures/html").joinpath(name).read_text(encoding="utf-8")


def _make_raw_site(
    html: str,
    url: str = "https://example.com",
    headers: dict[str, str] | None = None,
) -> RawSite:
    page = RawPage(
        url=url,
        final_url=url,
        status_code=200,
        headers=headers or {"content-type": "text/html"},
        html=html,
    )
    return RawSite(target_url=url, pages=[page], sitemap_urls=[])


def _parse(
    html: str,
    url: str = "https://example.com",
    headers: dict[str, str] | None = None,
) -> TechnologyResult:
    raw_site = _make_raw_site(html, url, headers)
    parsed = parse(raw_site)
    return detect_technology(raw_site, parsed)


def _get_techs(result: TechnologyResult, url: str | None = None) -> list:
    if url is None:
        return result.pages[0].technologies
    for page in result.pages:
        if page.url == url:
            return page.technologies
    return []


def _tech_names(technologies: list) -> set[str]:
    return {t.name for t in technologies}


class TestWordPress:
    def test_wordpress_detected(self) -> None:
        html = _load_fixture("wordpress-tech.html")
        result = _parse(html)
        assert "WordPress" in _tech_names(_get_techs(result))

    def test_wordpress_version_extracted(self) -> None:
        html = _load_fixture("wordpress-tech.html")
        result = _parse(html)
        wp = next(t for t in _get_techs(result) if t.name == "WordPress")
        assert wp.version == "6.4"

    def test_wordpress_confidence_high(self) -> None:
        html = _load_fixture("wordpress-tech.html")
        result = _parse(html)
        wp = next(t for t in _get_techs(result) if t.name == "WordPress")
        assert wp.confidence == "high"


class TestNextJS:
    def test_nextjs_detected(self) -> None:
        html = _load_fixture("nextjs-tech.html")
        result = _parse(html)
        assert "Next.js" in _tech_names(_get_techs(result))

    def test_nextjs_confidence_high(self) -> None:
        html = _load_fixture("nextjs-tech.html")
        result = _parse(html)
        tech = next(t for t in _get_techs(result) if t.name == "Next.js")
        assert tech.confidence == "high"


class TestReact:
    def test_react_detected(self) -> None:
        html = _load_fixture("react-tech.html")
        result = _parse(html)
        assert "React" in _tech_names(_get_techs(result))

    def test_react_confidence_medium(self) -> None:
        html = _load_fixture("react-tech.html")
        result = _parse(html)
        tech = next(t for t in _get_techs(result) if t.name == "React")
        assert tech.confidence == "medium"


class TestShopify:
    def test_shopify_detected(self) -> None:
        html = _load_fixture("shopify-tech.html")
        result = _parse(html)
        assert "Shopify" in _tech_names(_get_techs(result))

    def test_shopify_confidence_high(self) -> None:
        html = _load_fixture("shopify-tech.html")
        result = _parse(html)
        tech = next(t for t in _get_techs(result) if t.name == "Shopify")
        assert tech.confidence == "high"


class TestNginx:
    def test_nginx_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Server": "nginx/1.25.0"})
        assert "nginx" in _tech_names(_get_techs(result))

    def test_nginx_confidence_high(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Server": "nginx/1.25.0"})
        tech = next(t for t in _get_techs(result) if t.name == "nginx")
        assert tech.confidence == "high"


class TestApache:
    def test_apache_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Server": "Apache/2.4.57"})
        assert "Apache" in _tech_names(_get_techs(result))

    def test_apache_confidence_high(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Server": "Apache/2.4.57"})
        tech = next(t for t in _get_techs(result) if t.name == "Apache")
        assert tech.confidence == "high"


class TestBootstrap:
    def test_bootstrap_detected(self) -> None:
        html = _load_fixture("bootstrap-tech.html")
        result = _parse(html)
        assert "Bootstrap" in _tech_names(_get_techs(result))

    def test_bootstrap_confidence_high(self) -> None:
        html = _load_fixture("bootstrap-tech.html")
        result = _parse(html)
        tech = next(t for t in _get_techs(result) if t.name == "Bootstrap")
        assert tech.confidence == "high"


class TestTailwind:
    def test_tailwind_detected(self) -> None:
        html = _load_fixture("tailwind-tech.html")
        result = _parse(html)
        assert "Tailwind CSS" in _tech_names(_get_techs(result))

    def test_tailwind_confidence_high(self) -> None:
        html = _load_fixture("tailwind-tech.html")
        result = _parse(html)
        tech = next(t for t in _get_techs(result) if t.name == "Tailwind CSS")
        assert tech.confidence == "high"


class TestAnalytics:
    def test_google_analytics_detected(self) -> None:
        html = _load_fixture("analytics-tech.html")
        result = _parse(html)
        assert "Google Analytics" in _tech_names(_get_techs(result))

    def test_google_tag_manager_detected(self) -> None:
        html = _load_fixture("analytics-tech.html")
        result = _parse(html)
        assert "Google Tag Manager" in _tech_names(_get_techs(result))


class TestUnknownSite:
    def test_unknown_site_returns_empty(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html)
        assert _get_techs(result) == []


class TestMultipleTechnologies:
    def test_multiple_technologies_detected(self) -> None:
        html = _load_fixture("multi-tech.html")
        result = _parse(html)
        names = _tech_names(_get_techs(result))
        assert "WordPress" in names
        assert "Bootstrap" in names
        assert "Shopify" in names

    def test_multiple_pages_independent(self) -> None:
        wp_html = _load_fixture("wordpress-tech.html")
        raw_site = RawSite(
            target_url="https://example.com",
            pages=[
                RawPage(
                    url="https://example.com/",
                    final_url="https://example.com/",
                    status_code=200,
                    headers={"content-type": "text/html"},
                    html=wp_html,
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
        result = detect_technology(raw_site, parsed)
        assert len(result.pages) == 2
        assert _tech_names(_get_techs(result, "https://example.com/")) == {"WordPress"}
        assert _tech_names(_get_techs(result, "https://example.com/about")) == set()


class TestProvenance:
    def test_provenance_preserved(self) -> None:
        html = _load_fixture("wordpress-tech.html")
        result = _parse(html)
        wp = next(t for t in _get_techs(result) if t.name == "WordPress")
        assert len(wp.evidence) > 0
        assert wp.evidence[0].page_url == "https://example.com"
        assert wp.evidence[0].detection_rule == "meta_generator_wordpress"
        assert wp.evidence[0].source == "meta"


class TestGitHub:
    def test_github_server_detected(self) -> None:
        html = _load_fixture("github.html")
        result = _parse(html, headers={"server": "github.com"})
        assert "GitHub" in _tech_names(_get_techs(result))

    def test_github_server_case_insensitive(self) -> None:
        html = _load_fixture("github.html")
        result = _parse(html, headers={"Server": "github.com"})
        assert "GitHub" in _tech_names(_get_techs(result))

    def test_primer_css_detected(self) -> None:
        html = _load_fixture("github.html")
        result = _parse(html)
        assert "Primer CSS" in _tech_names(_get_techs(result))

    def test_turbo_detected_from_meta(self) -> None:
        html = _load_fixture("github.html")
        result = _parse(html)
        assert "Turbo/Hotwire" in _tech_names(_get_techs(result))

    def test_github_full_stack_detected(self) -> None:
        html = _load_fixture("github.html")
        result = _parse(html, headers={"server": "github.com"})
        names = _tech_names(_get_techs(result))
        assert "GitHub" in names
        assert "Primer CSS" in names
        assert "Turbo/Hotwire" in names


class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        html = _load_fixture("multi-tech.html")
        result1 = _parse(html)
        result2 = _parse(html)
        assert _tech_names(_get_techs(result1)) == _tech_names(_get_techs(result2))


class TestXPtoweredBy:
    def test_aspnet_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"X-Powered-By": "ASP.NET"})
        assert "ASP.NET" in _tech_names(_get_techs(result))

    def test_php_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"X-Powered-By": "PHP/8.1"})
        assert "PHP" in _tech_names(_get_techs(result))

    def test_express_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"X-Powered-By": "Express"})
        assert "Express.js" in _tech_names(_get_techs(result))


class TestCDNHeaders:
    def test_cloudflare_cf_ray(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"CF-RAY": "abc123"})
        assert "Cloudflare" in _tech_names(_get_techs(result))

    def test_cdn_via_header(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Via": "1.1 varnish"})
        assert "CDN/Proxy" in _tech_names(_get_techs(result))

    def test_fastly_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"X-Fastly": "123"})
        assert "Fastly" in _tech_names(_get_techs(result))

    def test_aws_cloudfront_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"X-Amz-Cf-Id": "abc123"})
        assert "AWS CloudFront" in _tech_names(_get_techs(result))


class TestSecurityHeaders:
    def test_csp_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Content-Security-Policy": "default-src 'self'"})
        assert "Content-Security-Policy" in _tech_names(_get_techs(result))

    def test_hsts_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Strict-Transport-Security": "max-age=31536000"})
        assert "HSTS" in _tech_names(_get_techs(result))

    def test_x_frame_options_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"X-Frame-Options": "DENY"})
        assert "X-Frame-Options" in _tech_names(_get_techs(result))

    def test_x_content_type_options_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"X-Content-Type-Options": "nosniff"})
        assert "X-Content-Type-Options" in _tech_names(_get_techs(result))

    def test_referrer_policy_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Referrer-Policy": "strict-origin-when-cross-origin"})
        assert "Referrer-Policy" in _tech_names(_get_techs(result))

    def test_permissions_policy_detected(self) -> None:
        html = _load_fixture("minimal.html")
        result = _parse(html, headers={"Permissions-Policy": "geolocation=()"})
        assert "Permissions-Policy" in _tech_names(_get_techs(result))


class TestNewJSLibraries:
    def test_jquery_ui_detected(self) -> None:
        html = '<html><head><script src="/js/jquery-ui.min.js"></script></head><body></body></html>'
        result = _parse(html)
        assert "jQuery UI" in _tech_names(_get_techs(result))

    def test_lodash_detected(self) -> None:
        html = '<html><head><script src="/js/lodash.min.js"></script></head><body></body></html>'
        result = _parse(html)
        assert "Lodash" in _tech_names(_get_techs(result))

    def test_moment_detected(self) -> None:
        html = '<html><head><script src="/js/moment.min.js"></script></head><body></body></html>'
        result = _parse(html)
        assert "Moment.js" in _tech_names(_get_techs(result))

    def test_axios_detected(self) -> None:
        html = '<html><head><script src="/js/axios.min.js"></script></head><body></body></html>'
        result = _parse(html)
        assert "Axios" in _tech_names(_get_techs(result))

    def test_gsap_detected(self) -> None:
        html = '<html><head><script src="/js/gsap.min.js"></script></head><body></body></html>'
        result = _parse(html)
        assert "GSAP" in _tech_names(_get_techs(result))

    def test_font_awesome_detected(self) -> None:
        html = '<html><head><script src="/js/fontawesome.js"></script></head><body></body></html>'
        result = _parse(html)
        assert "Font Awesome" in _tech_names(_get_techs(result))

    def test_hotjar_detected(self) -> None:
        html = '<html><head><script src="/js/hotjar.js"></script></head><body></body></html>'
        result = _parse(html)
        assert "Hotjar" in _tech_names(_get_techs(result))

    def test_stripe_detected(self) -> None:
        html = '<html><head><script src="https://js.stripe.com/v3/"></script></head><body></body></html>'
        result = _parse(html)
        assert "Stripe" in _tech_names(_get_techs(result))

    def test_swiper_detected(self) -> None:
        html = '<html><head><script src="/js/swiper.min.js"></script></head><body></body></html>'
        result = _parse(html)
        assert "Swiper" in _tech_names(_get_techs(result))


class TestHTMLCommentFingerprints:
    def test_wordpress_comment_detected(self) -> None:
        html = '<html><body><!-- WordPress 6.4 --><p>Content</p></body></html>'
        result = _parse(html)
        assert "WordPress" in _tech_names(_get_techs(result))

    def test_drupal_comment_detected(self) -> None:
        html = '<html><body><!-- Drupal 10 --><p>Content</p></body></html>'
        result = _parse(html)
        assert "Drupal" in _tech_names(_get_techs(result))


class TestJSGlobals:
    def test_nextjs_global_detected(self) -> None:
        html = '<html><head></head><body><script>window.__NEXT_DATA__ = {};</script></body></html>'
        result = _parse(html)
        assert "Next.js" in _tech_names(_get_techs(result))

    def test_nuxt_global_detected(self) -> None:
        html = '<html><head></head><body><script>window.__NUXT__ = {};</script></body></html>'
        result = _parse(html)
        assert "Nuxt" in _tech_names(_get_techs(result))
