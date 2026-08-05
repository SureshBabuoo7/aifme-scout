"""Summary Builder module.

Produces a deterministic, evidence-linked descriptive summary from a
ScoutSchema. In no-LLM mode the summary is template-based and derives
every claim from collected evidence. In LLM mode the implementation
falls back to the same template-based summary when no provider is
configured; LLM-backed generation is intentionally deferred to keep
this milestone within the frozen Architecture spec.

This module is presentation-only. It does not modify, add, or infer
evidence; it formats what the scanner, parser, extractors, and evidence
collector already produced.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from typing import TYPE_CHECKING

from aifme_scout.exporters.renderers import (
    bullet_list,
    clean_text,
    hr,
    humanize_label,
    humanize_value,
    join_sections,
    key_value_pairs,
    rating,
    score_bar,
    section,
    status_badge,
    table,
    truncate_text,
)
from aifme_scout.extractors.models import (
    EvidenceItem,
    ScoutSchema,
)
from aifme_scout.utils.constants import ScanMode
from aifme_scout.utils.models import Summary

if TYPE_CHECKING:
    pass

_VERSION = "1.0.0"
_REPO_URL = "https://github.com/SureshBabuoo7/aifme-scout"
_PYPI_URL = "https://pypi.org/project/aifme-scout/"

_NAVIGATION_NOISE = {
    "back to top",
    "menu",
    "reset",
    "smaller",
    "larger",
    "close",
    "skip to content",
    "aa",
    "search",
    "toggle navigation",
    "toggle menu",
}
_COVERAGE_THRESHOLD = 70
_SCAN_COVERAGE_THRESHOLD = 70

_LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "nl": "Dutch",
    "ar": "Arabic",
    "hi": "Hindi",
    "sv": "Swedish",
    "pl": "Polish",
    "tr": "Turkish",
}

_CATEGORY_EXPLANATIONS = {
    "frontend": "User interface framework",
    "backend": "Server-side technology",
    "cms": "Content management system",
    "e-commerce": "Online store platform",
    "analytics": "Traffic analytics tool",
    "language": "Programming language",
    "framework": "Development framework",
    "web-server": "Web server software",
    "web server": "Web server software",
    "hosting": "Hosting provider",
    "infrastructure": "Infrastructure / delivery",
    "security": "Security control",
    "icon library": "Icon library",
    "css framework": "Styling framework",
    "saas": "SaaS platform component",
    "crm": "Customer relationship tool",
    "email marketing": "Email marketing tool",
    "customer support": "Customer support tool",
    "payment": "Payment provider",
    "javascript library": "JavaScript library",
    "website builder": "Website builder",
}

_DETECTION_METHOD_LABELS = {
    "dom_signature": "DOM signature",
    "html_comment": "HTML comment fingerprint",
    "http_header": "HTTP response header",
    "js_global": "JavaScript global variable",
    "link_url": "Linked asset URL",
    "meta_generator": "Meta generator tag",
    "meta_tag": "Meta tag",
    "script_url": "Script URL",
}

_CHALLENGE_TITLES = {
    "just a moment",
    "attention required",
    "checking your browser",
    "access denied",
    "are you a human",
    "security challenge",
    "ddos protection",
}


def _evidence_text(item: EvidenceItem) -> str:
    """Best human-readable string for an evidence item's value."""
    return humanize_value(item.value, empty="")


def _plain_text(item: EvidenceItem) -> str:
    """Flatten an evidence value to plain text for keyword matching."""
    value = item.value
    if isinstance(value, dict):
        parts = [str(v) for v in value.values() if v]
        return " ".join(parts).lower()
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, list):
        return " ".join(str(v) for v in value).lower()
    return "" if value is None else str(value).lower()


def _collect_full_text(schema: ScoutSchema) -> str:
    """Concatenate all evidence text for deterministic keyword analysis."""
    parts: list[str] = []
    for item in schema.content:
        parts.append(_plain_text(item))
        if item.evidence_type in ("CONTENT_HEADING", "CONTENT_PARAGRAPH"):
            parts.append(_plain_text(item))
    for item in schema.seo:
        if item.evidence_type == "SEO_TITLE":
            parts.append(_plain_text(item))
    for item in schema.technology:
        parts.append(_plain_text(item))
    return " ".join(parts)


def _detect_access_limitations(schema: ScoutSchema) -> list[str]:
    """Detect deterministic signals of restricted scan coverage."""
    limitations: list[str] = []

    for item in schema.evidence:
        if item.evidence_type == "ANTI_BOT_CHALLENGE":
            limitations.append(
                "Anti-bot challenge detected (e.g., Cloudflare, Imperva, "
                "DataDome). The scanner could not reach the rendered page."
            )
            break

    if not limitations:
        for item in schema.seo:
            if item.evidence_type == "SEO_TITLE" and item.value:
                title = str(item.value).lower()
                if any(phrase in title for phrase in _CHALLENGE_TITLES):
                    limitations.append(
                        "Anti-bot challenge detected (e.g., Cloudflare, Imperva, "
                        "DataDome). The scanner could not reach the rendered page."
                    )
                    break

    if not limitations and any(i.evidence_type == "RATE_LIMITED" for i in schema.evidence):
        limitations.append(
            "The target rate-limited the scan (HTTP 429). Some pages may not have been analysed."
        )

    xml_pages = [i for i in schema.evidence if i.evidence_type == "XML_RESPONSE"]
    if xml_pages:
        xml_types = {str(i.value) for i in xml_pages if i.value}
        xml_detail = ", ".join(sorted(xml_types)) if xml_types else "XML"
        limitations.append(
            f"The requested URL returned {xml_detail} content rather than an HTML webpage. "
            "This commonly occurs for sitemap or feed endpoints. "
            "The website content could not be analysed from this response."
        )

    no_page_content = not schema.content and not schema.seo
    if no_page_content and not limitations and schema.evidence:
        limitations.append(
            "No page content was retrieved. The target may be protected by "
            "robots.txt rules, access restrictions, or a JavaScript-rendered app."
        )
    return limitations


def _detect_xml_limitation(schema: ScoutSchema) -> list[str]:
    """Return limitation text when the scan returned XML rather than HTML."""
    xml_pages = [i for i in schema.evidence if i.evidence_type == "XML_RESPONSE"]
    if not xml_pages:
        return []
    xml_types = {str(i.value) for i in xml_pages if i.value}
    if "sitemap" in xml_types and not xml_types - {"sitemap"}:
        return [
            (
                "The requested URL returned an XML sitemap rather than an HTML webpage. "
                "Sitemap URLs were extracted and scanned where possible."
            ),
        ]
    xml_detail = ", ".join(sorted(xml_types)) if xml_types else "XML"
    return [
        (
            f"The requested URL returned {xml_detail} content rather than an HTML webpage. "
            "This commonly occurs for sitemap or feed endpoints."
        ),
    ]


def _classify_target(schema: ScoutSchema) -> tuple[str, str]:
    """Classify the target site using only deterministic evidence.

    Returns ``(internal_key, confidence)`` where ``internal_key`` is the
    canonical classification used by the public API and ``confidence`` is a
    plain-language coverage note.
    """
    tech_names: set[str] = set()
    for item in schema.technology:
        if isinstance(item.value, dict):
            name = item.value.get("name")
            if isinstance(name, str):
                tech_names.add(name.lower())

    full_text = _collect_full_text(schema)
    title_text = ""
    for item in schema.seo:
        if item.evidence_type == "SEO_TITLE" and isinstance(item.value, str):
            title_text = item.value.lower()
            break
    heading_text = ""
    for item in schema.content:
        if item.evidence_type == "CONTENT_HEADING":
            heading_text += " " + _plain_text(item)
    title_or_heading = f"{title_text} {heading_text}"

    language_names = {
        "python",
        "java",
        "javascript",
        "typescript",
        "ruby",
        "go",
        "rust",
        "php",
        "c++",
        "c#",
        "kotlin",
        "swift",
        "scala",
        "dart",
        "elixir",
        "haskell",
        "perl",
        "r",
        "lua",
        "julia",
        "golang",
    }
    has_language_name = any(
        (name in title_text or re.search(r"(?<![a-z])" + re.escape(name) + r"(?![a-z])", full_text))
        for name in language_names
    )

    indicators = {
        "saas platform": (
            "saas",
            "api",
            "subscription",
            "trial",
            "cloud",
            "dashboard",
            "signup",
            "sign-up",
            "login",
            "demo",
            "pricing",
        ),
        "e-commerce platform": (
            "shopify",
            "woocommerce",
            "magento",
            "bigcommerce",
            "stripe",
            "paypal",
            "cart",
            "checkout",
            "shop",
            "store",
        ),
        "news publisher": (
            "newsroom",
            "breaking news",
            "latest news",
            "journalist",
            "editorial",
            "headline",
            "press release",
            "newsletter",
        ),
        "documentation platform": (
            "documentation",
            "docs",
            "tutorial",
            "reference",
            "api reference",
            "knowledge base",
            "help center",
            "manual",
            "guide",
        ),
        "corporate website": (
            "about us",
            "our team",
            "careers",
            "contact us",
            "company",
            "investor",
            "press",
            "leadership",
            "our company",
        ),
        "government portal": (
            "government",
            "official website",
            "public service",
            "citizen",
            "policy",
            "regulation",
            "gov",
        ),
        "educational institution": (
            "university",
            "college",
            "school",
            "education",
            "course",
            "student",
            "faculty",
            "academic",
            "campus",
        ),
        "media platform": (
            "watch",
            "listen",
            "episode",
            "podcast",
            "streaming",
            "channel",
            "video library",
            "media library",
        ),
        "agency website": (
            "agency",
            "client",
            "portfolio",
            "consulting",
            "case study",
            "our work",
            "what we do",
            "studio",
        ),
    }
    weights = {
        "saas platform": 1,
        "e-commerce platform": 1,
        "news publisher": 1,
        "documentation platform": 2,
        "corporate website": 1,
        "government portal": 1,
        "educational institution": 1,
        "media platform": 1,
        "agency website": 2,
    }

    def _hits(words: Iterable[str], text: str) -> int:
        score = 0
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"\b", text) or re.search(
                r"\b" + re.escape(word) + r"\w*\b", text
            ):
                score += 1
        return score

    scores: dict[str, int] = {}
    for category, words in indicators.items():
        base = _hits(words, full_text)
        tech_bonus = sum(2 for t in tech_names if t in words)
        weight = weights.get(category, 1)
        scores[category] = (base + tech_bonus) * weight

    doc_hits = _hits(indicators["documentation platform"], full_text)
    if doc_hits > 0 and has_language_name:
        scores["programming language documentation portal"] = (doc_hits + 3) * 2

    media_evidence = any(
        item.evidence_type in ("CONTENT_VIDEO", "CONTENT_AUDIO") for item in schema.content
    )
    if media_evidence:
        scores["media platform"] = 3

    best_category = max(scores, key=lambda k: scores[k])
    best_score = scores[best_category]

    keyword_strong = any(
        word in title_or_heading
        for word in (
            "saas",
            "shop",
            "shopify",
            "store",
            "news",
            "documentation",
            "docs",
            "university",
            "college",
            "school",
            "education",
            "course",
            "student",
            "faculty",
            "academic",
            "campus",
            "agency",
            "studio",
            "government",
            "corporate",
            "company",
            "media",
            "podcast",
            "video",
            "blog",
        )
    )
    qualifies = best_score >= 3 or (best_score >= 1 and keyword_strong)
    if not qualifies:
        return ("general website", "Determined from limited available signals")
    if best_category == "programming language documentation portal" and not has_language_name:
        return ("general website", "Determined from limited available signals")
    if best_category == "documentation platform" and not keyword_strong and not tech_names:
        return ("general website", "Determined from limited available signals")

    confidence = "Determined from multiple matching signals"
    return (best_category, confidence)


def _count_items(schema: ScoutSchema, category: str) -> int:
    """Count evidence items for a given schema category."""
    return len(getattr(schema, category, []))


def _count_unique_technologies(schema: ScoutSchema) -> int:
    """Count unique technology names in the schema."""
    seen: set[str] = set()
    for item in schema.technology:
        if isinstance(item.value, dict):
            name = item.value.get("name")
            if isinstance(name, str) and name:
                seen.add(name)
        elif isinstance(item.value, str):
            seen.add(item.value)
    return len(seen)


def _get_seo_status(item_value: object) -> tuple[str, str]:
    """Return (status_label, detail) for an SEO evidence value.

    The detail is always human-readable; raw Python objects are never
    returned to the caller.
    """
    if item_value is None:
        return ("NOT DETECTED", "Not detected")
    if isinstance(item_value, dict):
        noindex = item_value.get("noindex")
        if noindex is True:
            return ("NOINDEX", "Blocked from indexing")
        if noindex is False:
            return ("INDEXABLE", "Open to indexing")
        title = item_value.get("title")
        if title:
            return ("PASS", str(title))
        desc = item_value.get("description")
        if desc:
            return ("PASS", str(desc))
        url = item_value.get("url")
        if url:
            return ("PASS", str(url))
        has_json_ld = item_value.get("has_json_ld")
        if has_json_ld:
            kinds = []
            if has_json_ld:
                kinds.append("JSON-LD")
            if item_value.get("has_microdata"):
                kinds.append("Microdata")
            if item_value.get("has_rdfa"):
                kinds.append("RDFa")
            return ("PRESENT", ", ".join(kinds) or "Structured data")
        return ("PASS", "Detected")
    s = clean_text(str(item_value))
    if not s:
        return ("NOT DETECTED", "Not detected")
    return (
        "PASS",
        s.upper() if item_value is not None and str(item_value).lower().startswith("utf") else s,
    )


def _compute_health_score(schema: ScoutSchema) -> tuple[list[tuple[str, int]], int]:
    """Compute coverage scores for each signal area.

    Returns ``(scores, overall_score)`` where ``scores`` is a list of
    ``(area_label, score_0_100)`` tuples. Scores reflect how much of the
    available signal was captured in this scan, not absolute website quality.
    """
    scores: list[tuple[str, int]] = []
    weights = {
        "Website Reachability": 15,
        "Search Engine Optimization": 20,
        "Brand Metadata": 15,
        "Technology": 20,
        "Content": 20,
        "Social Presence": 10,
    }
    earned = 0
    total = sum(weights.values())

    site_reachable = bool(schema.site.url)
    if site_reachable:
        scores.append(("Website Reachability", 100))
        earned += weights["Website Reachability"]
    else:
        scores.append(("Website Reachability", 0))

    seo_items = schema.seo
    seo_score = 0
    if seo_items:
        checks = {
            "title": any(_evidence_text(i) for i in seo_items if i.evidence_type == "SEO_TITLE"),
            "meta_description": any(
                _evidence_text(i) for i in seo_items if i.evidence_type == "META_DESCRIPTION"
            ),
            "canonical": any(
                _evidence_text(i) for i in seo_items if i.evidence_type == "CANONICAL"
            ),
            "charset": any(_evidence_text(i) for i in seo_items if i.evidence_type == "CHARSET"),
            "viewport": any(_evidence_text(i) for i in seo_items if i.evidence_type == "VIEWPORT"),
            "language": any(_evidence_text(i) for i in seo_items if i.evidence_type == "LANGUAGE"),
            "robots": any(_evidence_text(i) for i in seo_items if i.evidence_type == "ROBOTS"),
            "indexability": any(
                _evidence_text(i) for i in seo_items if i.evidence_type == "INDEXABILITY"
            ),
        }
        passed = sum(1 for v in checks.values() if v)
        seo_score = int((passed / len(checks)) * 100) if checks else 0
    scores.append(("Search Engine Optimization", seo_score))
    earned += int(weights["Search Engine Optimization"] * seo_score / 100)

    metadata_items = schema.metadata
    metadata_score = 0
    if metadata_items:
        unique_types = {i.evidence_type for i in metadata_items}
        metadata_score = min(100, len(unique_types) * 15)
    scores.append(("Brand Metadata", metadata_score))
    earned += int(weights["Brand Metadata"] * metadata_score / 100)

    tech_items = schema.technology
    tech_score = 0
    if tech_items:
        seen: set[str] = set()
        unique_count = 0
        for item in tech_items:
            if isinstance(item.value, dict):
                name = item.value.get("name")
                if name and name not in seen:
                    seen.add(name)
                    unique_count += 1
        if unique_count >= 3:
            tech_score = 100
        elif unique_count == 2:
            tech_score = 75
        elif unique_count == 1:
            tech_score = 50
    scores.append(("Technology", tech_score))
    earned += int(weights["Technology"] * tech_score / 100)

    content_items = schema.content
    content_score = 0
    if content_items:
        if len(content_items) >= 10:
            content_score = 100
        elif len(content_items) >= 5:
            content_score = 75
        elif len(content_items) >= 1:
            content_score = 50
    scores.append(("Content", content_score))
    earned += int(weights["Content"] * content_score / 100)

    social_items = schema.social
    social_score = 0
    if social_items:
        seen_urls: set[str] = set()
        unique_count = 0
        for item in social_items:
            val = item.value
            if isinstance(val, dict):
                url = val.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_count += 1
        if unique_count >= 2:
            social_score = 100
        elif unique_count == 1:
            social_score = 75
    scores.append(("Social Presence", social_score))
    earned += int(weights["Social Presence"] * social_score / 100)

    overall = int(earned / total * 100) if total > 0 else 0
    return scores, overall


def _get_website_type(schema: ScoutSchema) -> str:
    classification, _ = _classify_target(schema)
    labels = {
        "e-commerce platform": "E-Commerce Store",
        "saas platform": "SaaS Platform",
        "news publisher": "News Website",
        "programming language documentation portal": "Programming Language Documentation Portal",
        "documentation platform": "Documentation Platform",
        "corporate website": "Corporate Website",
        "government portal": "Government Portal",
        "educational institution": "Educational Institution Website",
        "media platform": "Media Platform",
        "agency website": "Agency Website",
        "general website": "General Website",
    }
    return labels.get(classification, classification.title())


def _get_responsive(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "VIEWPORT" and item.value:
            return "Yes"
    for item in schema.content:
        val = _plain_text(item)
        if "viewport" in val and "width=device-width" in val:
            return "Yes"
    return "Unknown"


def _has_jsonld(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "STRUCTURED_DATA":
            val = item.value
            if isinstance(val, dict) and val.get("has_json_ld"):
                return "Detected"
            if isinstance(val, str) and "json" in val.lower():
                return "Detected"
    return "Not detected"


def _has_rss(schema: ScoutSchema) -> str:
    for item in schema.metadata:
        if item.evidence_type in ("RSS_FEED", "ATOM_FEED"):
            return "Available"
    return "Not available"


def _has_canonical(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "CANONICAL" and item.value:
            return "Yes"
    return "No"


def _get_language(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "LANGUAGE":
            val = item.value
            raw = val.get("value", "Unknown") if isinstance(val, dict) else val
            if not raw:
                return "Unknown"
            code = str(raw).split("-")[0].lower()
            return f"{_LANGUAGE_NAMES.get(code, raw)} ({raw})"
    return "Unknown"


def _get_charset(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "CHARSET" and item.value:
            return str(item.value).upper()
    return "Unknown"


def _get_robots_status(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "ROBOTS":
            val = item.value
            directive = str(val).lower() if val else ""
            if "noindex" in directive:
                return "Blocked (noindex)"
            if "nofollow" in directive:
                return "Links not followed"
            if directive:
                return "Configured"
            return "Configured"
    return "Not configured"


def _has_xml_pages(schema: ScoutSchema) -> bool:
    """Return True if any evidence item marks a page as a non-HTML XML response."""
    return any(item.evidence_type == "XML_RESPONSE" for item in schema.evidence)


def _scan_status(schema: ScoutSchema) -> tuple[str, str, list[str]]:
    """Determine the overall scan result and any coverage limitations."""
    limitations = _detect_access_limitations(schema)
    if not schema.evidence:
        return ("none", "No Data Collected", limitations)

    if limitations:
        return ("limited", "Limited Scan", limitations)

    core_present = bool(schema.seo) and bool(schema.technology) and bool(schema.content)
    _, coverage = _compute_health_score(schema)
    if core_present and coverage >= _SCAN_COVERAGE_THRESHOLD:
        return ("complete", "Full Scan", limitations)
    return ("partial", "Partial Scan", limitations)


def _build_title(schema: ScoutSchema) -> str:
    target = schema.site.target_url or schema.site.url
    date = schema.meta.timestamp[:10]
    return "\n".join(
        [
            "# Website Intelligence Report",
            "",
            f"**Target:** {target}",
            f"**Report Date:** {date}",
            f"**Generated By:** AIFME Scout OSS {_VERSION}",
        ]
    )


def _build_executive_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Executive Summary section."""
    lines: list[str] = []
    refs: list[str] = []

    target = schema.site.target_url or schema.site.url
    refs.append(target)

    status, status_label, limitations = _scan_status(schema)

    xml_limitations = _detect_xml_limitation(schema)
    if xml_limitations:
        limitations = list(limitations) + xml_limitations
        if status not in ("none",):
            status = "limited"
            status_label = "Limited Scan"
    scores, coverage = _compute_health_score(schema)
    ev_total = len(schema.evidence)

    if status == "none":
        confidence = "None"
    elif limitations:
        confidence = "Low"
    elif coverage >= 90 and status == "complete":
        confidence = "High"
    elif coverage >= 70:
        confidence = "Medium"
    else:
        confidence = "Low"

    lines.append(f"**Overall Status:** {status_label}")
    lines.append(f"**Signal Coverage:** {coverage}%")
    lines.append(f"**Evidence Collected:** {ev_total}")
    lines.append(f"**Confidence:** {confidence}")

    lines.append("")
    lines.append("**Scan Outcome at a Glance**")
    lines.append("")
    area_rows = [
        [
            "Search Engine Optimization",
            str(_count_items(schema, "seo")),
            rating(_area_score(scores, "Search Engine Optimization")),
        ],
        [
            "Brand Metadata",
            str(_count_items(schema, "metadata")),
            rating(_area_score(scores, "Brand Metadata")),
        ],
        [
            "Technology",
            str(_count_unique_technologies(schema)),
            rating(_area_score(scores, "Technology")),
        ],
        ["Content", str(_count_items(schema, "content")), rating(_area_score(scores, "Content"))],
        [
            "Social Profiles",
            str(_count_items(schema, "social")),
            rating(_area_score(scores, "Social Presence")),
        ],
        [
            "Competitive References",
            str(_count_items(schema, "competitors")),
            rating(
                _area_score(scores, "Social Presence") if _count_items(schema, "competitors") else 0
            ),
        ],
    ]
    lines.append(table(["Signal Area", "Items Collected", "Coverage"], area_rows))
    lines.append("")
    lines.append(
        "Coverage reflects how much of each signal area was captured in this "
        "scan. It is a measure of scan completeness, **not** of website quality "
        "or performance."
    )

    lines.append("")
    lines.append("**Overall Assessment**")
    lines.append("")
    classification = _get_website_type(schema)
    assessment = [f"{target} is classified as a **{classification}**."]
    if status == "complete":
        assessment.append(
            "This scan completed successfully and captured a comprehensive set of signals."
        )
    elif status == "partial":
        assessment.append(
            "This scan completed but captured only part of the available signal. "
            "Some areas may have been outside the scope of this scan."
        )
    elif status == "limited":
        assessment.append(
            "This scan produced limited results. Anti-bot protection, "
            "JavaScript rendering requirements, robots.txt restrictions, or "
            "access restrictions may have prevented full analysis."
        )
    else:
        assessment.append(
            "This scan did not return usable data for the target. The result may "
            "be caused by access restrictions rather than the website itself."
        )
    assessment.append(
        f"The assessment is based on {ev_total} evidence points covering "
        f"{coverage}% of available signals."
    )
    lines.append(" ".join(assessment))

    return "\n".join(lines), refs


def _area_score(scores: list[tuple[str, int]], area: str) -> int:
    """Return the numeric score for a given area label."""
    for label, score in scores:
        if label == area:
            return score
    return 0


def _build_health_score(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Signal Coverage section."""
    lines: list[str] = []
    refs: list[str] = []

    scores, overall = _compute_health_score(schema)
    rows = [[area, score_bar(score), status_badge(rating(score))] for area, score in scores]
    lines.append(table(["Signal Area", "Coverage Score", "Rating"], rows))
    lines.append("")
    lines.append(
        "Scores measure how much of each signal area this scan was able to "
        "collect. They reflect scan coverage, not the quality of the website. "
        "A low score in one area may mean the signal was simply not present in "
        "the scanned pages or was restricted by the target."
    )
    return "\n".join(lines), refs


def _build_website_overview(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Website Overview section."""
    lines: list[str] = []
    refs: list[str] = []

    target = schema.site.target_url or schema.site.url
    refs.append(target)

    classification = _get_website_type(schema)
    _, classification_confidence = _classify_target(schema)
    classification_confidence = _classification_confidence_label(classification_confidence)

    pairs: list[tuple[str, str]] = [
        ("Website URL", target),
        ("Website Category", classification),
        ("Classification Confidence", classification_confidence),
        ("Mobile-Friendly Design", _get_responsive(schema)),
        ("Structured Data", _has_jsonld(schema)),
        ("RSS Feeds", _has_rss(schema)),
        ("Canonical URL", _has_canonical(schema)),
        ("Primary Language", _get_language(schema)),
        ("Character Encoding", _get_charset(schema)),
        ("Search Engine Instructions", _get_robots_status(schema)),
    ]
    display = [(key, value) for key, value in pairs if value and value != "Unknown"]
    lines.append(key_value_pairs(display))

    # Add classification rationale
    classification_lines, classification_refs = _build_classification_details(schema)
    if classification_lines:
        lines.append("")
        lines.append(classification_lines)
        refs.extend(classification_refs)

    return "\n".join(lines), refs


def _build_scan_limitations(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Scan Limitations section when coverage was restricted."""
    lines: list[str] = []
    refs: list[str] = []

    _, _, limitations = _scan_status(schema)
    if not limitations:
        return "\n".join(lines), refs

    lines.append("The following factors may have limited this scan's coverage:")
    lines.append("")
    lines.extend(f"- {item}" for item in limitations)
    lines.append("")
    lines.append(
        "These factors affect scan coverage only, **not** the quality of the "
        "website. When a scan is restricted, the absence of a signal does not "
        "mean the signal is absent from the website. A follow-up scan with "
        "different settings may reveal additional detail."
    )
    return "\n".join(lines), refs


def _build_seo_analysis(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the SEO Analysis section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.seo:
        lines.append("No SEO evidence was collected during this scan.")
        lines.append("")
        lines.append(
            "Without SEO evidence, this scan cannot assess the target's search "
            "engine visibility. The absence of evidence here reflects scan "
            "coverage, not necessarily the website's configuration."
        )
        return "\n".join(lines), refs

    seo_checks = [
        ("Page Title", "SEO_TITLE", "Appears in search results and browser tabs"),
        ("Meta Description", "META_DESCRIPTION", "Influences search click-through rate"),
        ("Canonical URL", "CANONICAL", "Prevents duplicate content in search"),
        ("Search Engine Instructions", "ROBOTS", "Tells search engines which pages to index"),
        ("Primary Language", "LANGUAGE", "Helps search engines serve the right audience"),
        ("Character Encoding", "CHARSET", "Ensures text displays correctly for all visitors"),
        ("Mobile Viewport", "VIEWPORT", "Required for mobile-friendly ranking"),
    ]
    structured_checks = [
        ("Open Graph", "OPEN_GRAPH", "Controls how pages appear when shared socially"),
        ("Twitter Card", "TWITTER_CARD", "Controls how pages appear when shared on X/Twitter"),
        ("Structured Data", "STRUCTURED_DATA", "Helps search engines show rich results"),
    ]

    seo_map: dict[str, EvidenceItem] = {i.evidence_type: i for i in schema.seo}

    rows: list[list[str]] = []
    for label, evidence_type, impact in seo_checks:
        found = seo_map.get(evidence_type)
        if found is not None:
            status, detail = _get_seo_status(found.value)
            if evidence_type == "CHARSET" and detail:
                detail = detail.upper()
            display_value = detail if len(detail) <= 60 else truncate_text(detail, 60)
            rows.append([label, status_badge(status), display_value, impact])
            if found.evidence_id:
                refs.append(found.evidence_id)
        else:
            rows.append([label, "Not detected", "Not detected", impact])

    for label, evidence_type, impact in structured_checks:
        found = seo_map.get(evidence_type)
        if found is not None:
            status, detail = _get_seo_status(found.value)
            display_value = detail if len(detail) <= 60 else truncate_text(detail, 60)
            rows.append([label, status_badge(status), display_value, impact])
            if found.evidence_id:
                refs.append(found.evidence_id)
        else:
            rows.append([label, "Not detected", "Not detected", impact])

    lines.append(table(["SEO Element", "Status", "Detail", "Business Value"], rows))

    robots_evidence = seo_map.get("ROBOTS")
    indexability = next((i for i in schema.seo if i.evidence_type == "INDEXABILITY"), None)
    if indexability is not None or (robots_evidence is not None and robots_evidence.value):
        lines.append("")
        lines.append("### Search Engine Indexing Directives")
        lines.append("")
        directive_rows: list[list[str]] = []
        if indexability is not None and isinstance(indexability.value, dict):
            for key in ("noindex", "nofollow", "noarchive", "nosnippet"):
                flag = indexability.value.get(key)
                if isinstance(flag, bool):
                    label = humanize_label(key)
                    directive_rows.append([label, status_badge("YES" if flag else "NO")])
                    if flag:
                        directive_rows.append(
                            [f"{label} Effect", "Search engines will not honour this directive"]
                        )
                    else:
                        directive_rows.append(
                            [f"{label} Effect", "Search engines may index and follow normally"]
                        )
        if robots_evidence is not None and robots_evidence.value:
            raw = str(robots_evidence.value).lower()
            directive_rows.append(["Robots Meta Tag", clean_text(str(robots_evidence.value))])
            if "noindex" in raw:
                directive_rows.append(["Indexing", "Blocked from indexing"])
            if "nofollow" in raw:
                directive_rows.append(["Link Following", "Links not followed"])
        if directive_rows:
            lines.append(table(["Directive", "Value"], directive_rows))

    not_detected = [r[0] for r in rows if r[1] == "Not detected"]
    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    if not_detected:
        lines.append(
            f"The following SEO elements were not detected in the scanned page: "
            f"{', '.join(not_detected)}. Their absence here reflects scan "
            f"coverage, not necessarily a problem with the website."
        )
    else:
        lines.append(
            "All core SEO elements are present. The website is well-optimized for search engines."
        )

    return "\n".join(lines), refs


def _build_metadata_analysis(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Metadata Analysis section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.metadata:
        lines.append("No metadata evidence was collected during this scan.")
        return "\n".join(lines), refs

    brand_items: list[tuple[str, str]] = []
    favicons: list[str] = []
    rss_feeds: list[str] = []
    verification: list[str] = []

    for item in schema.metadata:
        val = item.value
        if item.evidence_type == "SITE_NAME" and val:
            brand_items.append(("Brand Name", str(val)))
        elif item.evidence_type == "APPLICATION_NAME" and val:
            brand_items.append(("Application Name", str(val)))
        elif item.evidence_type == "GENERATOR" and val:
            brand_items.append(("Generator", str(val)))
        elif item.evidence_type == "AUTHOR" and val:
            brand_items.append(("Author", str(val)))
        elif item.evidence_type == "PUBLISHER" and val:
            brand_items.append(("Publisher", str(val)))
        elif item.evidence_type == "COPYRIGHT" and val:
            brand_items.append(("Copyright", str(val)))
        elif item.evidence_type == "FAVICON" and val:
            favicons.append(str(val))
        elif item.evidence_type == "MANIFEST" and val:
            brand_items.append(("Web App Manifest", str(val)))
        elif item.evidence_type == "THEME_COLOR" and val:
            brand_items.append(("Theme Color", str(val)))
        elif item.evidence_type in ("RSS_FEED", "ATOM_FEED") and val:
            rss_feeds.append(str(val))
        elif item.evidence_type == "VERIFICATION_TAG" and isinstance(val, dict):
            platform = val.get("platform", "")
            value = val.get("value", "")
            if platform and value:
                verification.append(f"{platform.title()}: {value}")

    if brand_items:
        lines.append("### Brand & Identity")
        lines.append("")
        lines.append(key_value_pairs(brand_items))
        lines.append("")

    if favicons:
        lines.append("### Brand Assets")
        lines.append("")
        lines.append("Bookmark and app icons were detected.")
        lines.append("")

    if rss_feeds:
        lines.append("### Content Feeds")
        lines.append("")
        lines.append(bullet_list(rss_feeds[:5]))
        lines.append("")

    if verification:
        lines.append("### Search Engine Verification")
        lines.append("")
        lines.append(bullet_list(verification[:5]))
        lines.append("")

    lines.append("**Business Takeaway**")
    lines.append("")
    parts = []
    if brand_items:
        parts.append("a defined brand identity")
    if favicons:
        parts.append("bookmark icons")
    if rss_feeds:
        parts.append("content syndication feeds")
    if verification:
        parts.append("search engine verification")
    if parts:
        lines.append(f"Metadata confirms {', '.join(parts)}.")
    else:
        lines.append(
            "Limited brand metadata was detected. Additional metadata can improve "
            "how the website appears in search and on devices."
        )
    return "\n".join(lines), refs


def _readable_detection(method: str) -> str:
    return _DETECTION_METHOD_LABELS.get(method, clean_text(method))


def _build_technology_stack(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Technology Stack section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.technology:
        lines.append("No technology evidence was collected during this scan.")
        return "\n".join(lines), refs

    seen: set[str] = set()
    rows: list[list[str]] = []
    for item in schema.technology:
        val = item.value
        if isinstance(val, dict):
            name = str(val.get("name", "Unknown"))
            category = str(val.get("category", "Unknown"))
            confidence = str(val.get("confidence", "medium"))
        else:
            name = str(val)
            category = "Unknown"
            confidence = "medium"

        if name in seen:
            continue
        seen.add(name)

        purpose = _CATEGORY_EXPLANATIONS.get(category.lower(), humanize_label(category))
        rows.append([name, purpose, status_badge(confidence)])
        if item.evidence_id:
            refs.append(item.evidence_id)

    rows.sort(key=lambda r: r[0].lower())
    lines.append(table(["Technology", "Purpose", "Confidence"], rows))

    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    if rows:
        category_names = sorted({r[1] for r in rows})
        lines.append(
            f"The scan detected {len(rows)} technologies across "
            f"{len(category_names)} categories: {', '.join(category_names)}. "
            "Detection is based on observable signals such as response headers, "
            "page markup, and linked assets."
        )
    else:
        lines.append("No technology was detected during this scan.")
    return "\n".join(lines), refs


_BOILERPLATE = (
    "privacy",
    "terms of service",
    "terms of use",
    "cookie",
    "copyright",
    "all rights reserved",
    "legal",
    "sitemap",
    "contact us",
    "newsletter",
    "subscribe",
    "sign in",
    "log in",
    "menu",
    "skip to",
    "back to top",
    "accept",
    "close",
    "search",
)


def _is_boilerplate(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in _BOILERPLATE)


def _build_content_analysis(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Content Analysis section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.content:
        lines.append("No content evidence was collected during this scan.")
        lines.append("")
        lines.append(
            "JavaScript-heavy or access-restricted sites may not expose content "
            "to a server-side scan."
        )
        return "\n".join(lines), refs

    # Primary Topics
    topic_lines, topic_refs = _build_content_topics(schema)
    if topic_lines:
        lines.append(topic_lines)
        refs.extend(topic_refs)

    # Top Keywords
    keyword_lines, keyword_refs = _build_content_keywords(schema)
    if keyword_lines:
        lines.append(keyword_lines)
        refs.extend(keyword_refs)

    # Content Inventory
    counts: Counter[str] = Counter()
    for item in schema.content:
        counts[item.evidence_type] += 1

    lines.append("### Content Inventory")
    lines.append("")
    inventory = [
        ("Headings", counts.get("CONTENT_HEADING", 0)),
        ("Paragraphs", counts.get("CONTENT_PARAGRAPH", 0)),
        ("Lists", counts.get("CONTENT_LIST", 0)),
        ("Tables", counts.get("CONTENT_TABLE", 0)),
        ("Images", counts.get("IMAGE", 0)),
        ("Links", counts.get("LINK", 0)),
        ("Videos", counts.get("CONTENT_VIDEO", 0)),
        ("Audio", counts.get("CONTENT_AUDIO", 0)),
    ]
    lines.append(
        table(
            ["Content Type", "Count"], [[label, str(count)] for label, count in inventory if count]
        )
    )

    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    headings = [item for item in schema.content if item.evidence_type == "CONTENT_HEADING"]
    if headings:
        main_topic = _plain_text(headings[0]).title()
        lines.append(
            f'The page is organised around "{main_topic}". Clear, descriptive '
            "headings help visitors and search engines understand the content."
        )
    else:
        lines.append(
            "Content structure was limited in this scan. More structured content "
            "can improve engagement and search visibility."
        )
    return "\n".join(lines), refs


def _social_account_label(platform: str, username: str, url: str) -> str:
    """Derive the most useful account label from a social profile."""
    generic = {"company", "in", "channel", "user", "users", "profile", "profiles", "home", "intent"}
    if username and username.lower() not in generic:
        return f"{platform}: @{username}"
    from urllib.parse import urlparse

    path = urlparse(url).path.strip("/")
    if path:
        segment = path.split("/")[0]
        if segment and segment.lower() not in generic:
            return f"{platform}: {segment}"
    return f"{platform}: {url}"


def _build_social_presence(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Social Presence section."""
    return _build_social_presence_improved(schema)


def _build_competitive_signals(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Competitive Signals section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.competitors:
        lines.append("No competitive references were detected during this scan.")
        lines.append("")
        lines.append(
            "Scout only reports competitors that the target site explicitly names "
            "or links to. Their absence does not imply a lack of competition."
        )
        return "\n".join(lines), refs

    seen: set[str] = set()
    rows: list[list[str]] = []
    for item in schema.competitors:
        val = item.value
        if isinstance(val, dict):
            name = str(val.get("name", "Unknown"))
            url = str(val.get("url", "") or "")
        else:
            name = str(val)
            url = ""
        if name in seen:
            continue
        seen.add(name)
        rows.append([name, url if url else "Not available"])
        if item.evidence_id:
            refs.append(item.evidence_id)

    if len(rows) == 1:
        lines.append(f"**Competitor:** {rows[0][0]}")
        if rows[0][1] != "Not available":
            lines.append(f"**URL:** {rows[0][1]}")
    elif rows:
        lines.append(table(["Competitor", "Reference"], rows))
    else:
        lines.append("No competitive references were detected during this scan.")

    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    lines.append(
        f"Competitor awareness helps the business stay competitive. "
        f"{len(rows)} competitor reference(s) were identified for further analysis."
    )
    return "\n".join(lines), refs


def _build_strengths(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Top Strengths section."""
    return _build_strengths_improved(schema)


def _build_weaknesses(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Improvement Opportunities section."""
    return _build_weaknesses_improved(schema)


def _build_recommendations(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Executive Recommendations section."""
    return _build_recommendations_improved(schema)


def _build_executive_scorecard(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Executive Scorecard section."""
    lines: list[str] = []
    refs: list[str] = []

    scores, overall = _compute_health_score(schema)
    score_map = dict(scores)

    def _level(score: int) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 70:
            return "Good"
        if score >= 40:
            return "Partial"
        if score > 0:
            return "Limited"
        return "Not collected"

    rows = [
        ["Scan Coverage", _level(score_map.get("Website Reachability", 0))],
        ["Brand Metadata", _level(score_map.get("Brand Metadata", 0))],
        ["Technology Signals", _level(score_map.get("Technology", 0))],
        ["Content Coverage", _level(score_map.get("Content", 0))],
        ["Social Presence", _level(score_map.get("Social Presence", 0))],
        ["SEO Coverage", _level(score_map.get("Search Engine Optimization", 0))],
    ]
    lines.append(table(["Area", "Status"], rows))
    return "\n".join(lines), refs


def _build_business_snapshot(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Business Snapshot section."""
    lines: list[str] = []
    refs: list[str] = []

    classification, _ = _classify_target(schema)
    display_classification = _get_website_type(schema)

    # Primary Audience - deterministic extraction from content
    audience_signals = _extract_audience_signals(schema)
    primary_audience = (
        ", ".join(audience_signals)
        if audience_signals else "Not enough evidence collected"
    )

    # Content Strategy - from content types present
    content_strategy = _determine_content_strategy(schema)

    # Brand Presence - from metadata and social evidence
    brand_presence = _assess_brand_presence(schema)

    # Technology Maturity - from technology evidence
    tech_maturity = _assess_tech_maturity(schema)

    # Content Depth - from content counts
    content_depth = _assess_content_depth(schema)

    # Digital Footprint - from social and competitor counts
    digital_footprint = _assess_digital_footprint(schema)

    pairs = [
        ("Business Category", display_classification),
        ("Primary Audience", primary_audience),
        ("Content Strategy", content_strategy),
        ("Brand Presence", brand_presence),
        ("Technology Maturity", tech_maturity),
        ("Content Depth", content_depth),
        ("Digital Footprint", digital_footprint),
    ]
    display = [(key, value) for key, value in pairs if value and value != "Unknown"]
    lines.append(key_value_pairs(display))
    return "\n".join(lines), refs


def _extract_audience_signals(schema: ScoutSchema) -> list[str]:
    """Extract primary audience signals from content evidence."""
    signals: set[str] = set()
    audience_keywords = {
        "developers": "Developers",
        "developer": "Developers",
        "students": "Students",
        "student": "Students",
        "engineers": "Engineering Teams",
        "engineering": "Engineering Teams",
        "teams": "Engineering Teams",
        "team": "Engineering Teams",
        "businesses": "Businesses",
        "business": "Businesses",
        "enterprise": "Enterprise",
        "agencies": "Agencies",
        "agency": "Agencies",
        "creators": "Creators",
        "publishers": "Publishers",
        "consumers": "Consumers",
        "customers": "Customers",
        "users": "Users",
        "teachers": "Educators",
        "education": "Educators",
        "learners": "Learners",
        "researchers": "Researchers",
        "startups": "Startups",
        "founders": "Founders",
        "investors": "Investors",
        "marketers": "Marketers",
        "designers": "Designers",
        "freelancers": "Freelancers",
        "owners": "Business Owners",
        "everyone": "General Audience",
        "all": "General Audience",
    }
    full_text = _collect_full_text(schema)
    for keyword, label in audience_keywords.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", full_text):
            signals.add(label)
    return sorted(signals)[:4]


def _determine_content_strategy(schema: ScoutSchema) -> str:
    """Determine content strategy from evidence."""
    strategies: set[str] = set()
    if any(
        i.evidence_type == "RSS_FEED" or i.evidence_type == "ATOM_FEED"
        for i in schema.metadata
    ):
        strategies.add("Content syndication")
    if any(i.evidence_type == "CONTENT_HEADING" for i in schema.content):
        text = " ".join(
            _plain_text(i) for i in schema.content
            if i.evidence_type == "CONTENT_HEADING"
        )
        if "tutorial" in text.lower() or "guide" in text.lower() or "learn" in text.lower():
            strategies.add("Tutorials")
        if "download" in text.lower():
            strategies.add("Downloads")
        if "news" in text.lower() or "blog" in text.lower() or "article" in text.lower():
            strategies.add("News / Blog")
        if "documentation" in text.lower() or "docs" in text.lower() or "reference" in text.lower():
            strategies.add("Documentation")
    if any(i.evidence_type == "CONTENT_FORM" for i in schema.content):
        strategies.add("Lead generation")
    if any(i.evidence_type in ("CONTENT_IMAGE", "CONTENT_VIDEO", "CONTENT_AUDIO")
           for i in schema.content):
        strategies.add("Media-rich content")
    if not strategies:
        return "Not enough evidence collected"
    return ", ".join(sorted(strategies))


def _assess_brand_presence(schema: ScoutSchema) -> str:
    """Assess brand presence from metadata and social evidence."""
    meta_score = len(schema.metadata)
    social_score = len(schema.social)
    if meta_score >= 5 and social_score >= 3:
        return "Strong"
    if meta_score >= 2 or social_score >= 1:
        return "Moderate"
    if meta_score == 0 and social_score == 0:
        return "Not enough evidence collected"
    return "Limited"


def _assess_tech_maturity(schema: ScoutSchema) -> str:
    """Assess technology maturity from technology evidence."""
    if not schema.technology:
        return "Not enough evidence collected"
    seen_names: set[str] = set()
    modern_indicators = 0
    for item in schema.technology:
        if isinstance(item.value, dict):
            name = str(item.value.get("name", "")).lower()
            if name and name not in seen_names:
                seen_names.add(name)
                if name in {
                    "react", "next.js", "vue", "nuxt", "angular", "svelte",
                    "wordpress", "shopify", "cloudflare", "nginx", "hsts",
                    "csp", "x-frame-options", "x-content-type-options",
                    "bootstrap", "tailwind css", "jquery", "google analytics",
                    "gtm", "plausible", "matomo", "vercel", "netlify",
                }:
                    modern_indicators += 1
    if modern_indicators >= 3:
        return "Modern"
    if modern_indicators >= 1:
        return "Standard"
    return "Basic"


def _assess_content_depth(schema: ScoutSchema) -> str:
    """Assess content depth from content evidence counts."""
    content_count = len(schema.content)
    if content_count >= 50:
        return "Extensive"
    if content_count >= 10:
        return "Moderate"
    if content_count >= 1:
        return "Limited"
    return "Not enough evidence collected"


def _assess_digital_footprint(schema: ScoutSchema) -> str:
    """Assess digital footprint from social and competitor evidence."""
    social_count = len(schema.social)
    competitor_count = len(schema.competitors)
    total = social_count + competitor_count
    if total >= 5:
        return "High"
    if total >= 2:
        return "Moderate"
    if total >= 1:
        return "Limited"
    return "Not enough evidence collected"


def _build_technology_maturity(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Technology Maturity section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.technology:
        lines.append("No technology evidence was collected during this scan.")
        return "\n".join(lines), refs

    seen_names: set[str] = set()
    categories: set[str] = set()
    security_signals = False
    cdn_signals = False
    modern_frontend = False
    performance_signals = False

    for item in schema.technology:
        if isinstance(item.value, dict):
            name = str(item.value.get("name", ""))
            category = str(item.value.get("category", ""))
            if name and name not in seen_names:
                seen_names.add(name)
                categories.add(category)
            if category in ("security", "infrastructure"):
                security_signals = True
            if category in ("infrastructure", "cdn", "hosting"):
                cdn_signals = True
            if category in ("frontend", "framework", "css framework"):
                modern_frontend = True
            if name.lower() in {
                "hsts", "csp", "x-frame-options",
                "x-content-type-options", "preload"
            }:
                performance_signals = True
            if item.evidence_id:
                refs.append(item.evidence_id)

    # Infrastructure
    infrastructure = (
        "Modern" if cdn_signals else "Standard" if categories
        else "Not enough evidence collected"
    )
    # Security
    security = (
        "Strong" if security_signals else "Standard" if categories
        else "Not enough evidence collected"
    )
    # Client Technologies
    client = (
        "Modern" if modern_frontend else "Standard" if categories
        else "Not enough evidence collected"
    )
    # Performance Signals
    performance = (
        "Detected" if performance_signals
        else "Not detected" if categories
        else "Not enough evidence collected"
    )

    rows = [
        ["Infrastructure", infrastructure],
        ["Security", security],
        ["Client Technologies", client],
        ["Performance Signals", performance],
    ]
    lines.append(table(["Area", "Assessment"], rows))
    return "\n".join(lines), refs


def _classification_confidence_label(confidence: str) -> str:
    """Map classification confidence string to executive label."""
    if "multiple matching signals" in confidence:
        return "High"
    if "limited available signals" in confidence:
        return "Low"
    return confidence


def _build_classification_details(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build classification confidence and rationale."""
    lines: list[str] = []
    refs: list[str] = []

    classification, confidence = _classify_target(schema)
    confidence_label = _classification_confidence_label(confidence)

    lines.append("### Classification Confidence")
    lines.append("")
    lines.append(confidence_label)
    lines.append("")

    lines.append("### Classification Based On")
    lines.append("")

    # Deterministic signals that contributed to classification
    signals: list[str] = []
    full_text = _collect_full_text(schema)
    title_text = ""
    for item in schema.seo:
        if item.evidence_type == "SEO_TITLE" and isinstance(item.value, str):
            title_text = item.value.lower()
            break

    if "documentation" in full_text or "docs" in full_text or "tutorial" in full_text:
        signals.append("Documentation content")
    if "api reference" in full_text or "reference" in full_text:
        signals.append("Reference material")
    if any(name in title_text or name in full_text
           for name in ["python", "java", "javascript", "typescript",
                        "ruby", "go", "rust", "php"]):
        signals.append("Programming language association")
    if any(word in full_text
           for word in ["developer", "developers", "engineering",
                        "engineering team"]):
        signals.append("Developer ecosystem")
    if any(item.evidence_type == "OPEN_GRAPH" for item in schema.seo):
        signals.append("Official branding")
    if len(schema.technology) >= 3:
        signals.append("Multiple supporting signals")
    if any(item.evidence_type in ("RSS_FEED", "ATOM_FEED") for item in schema.metadata):
        signals.append("Content feeds")
    if any(item.evidence_type == "SITE_NAME" for item in schema.metadata):
        signals.append("Brand identity")

    if not signals:
        signals.append("General website signals")

    for signal in sorted(signals)[:6]:
        lines.append(f"- {signal}")
    return "\n".join(lines), refs


def _build_content_keywords(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Top Keywords section from content evidence."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.content and not schema.seo:
        return "\n".join(lines), refs

    word_counts: Counter[str] = Counter()
    stop_words = {
        "the", "and", "for", "with", "from", "that", "this", "have", "has", "been",
        "were", "was", "are", "not", "but", "they", "their", "will", "would", "can",
        "all", "your", "more", "some", "what", "when", "how", "why", "which", "each",
        "also", "than", "other", "into", "over", "such", "after", "before", "between",
        "under", "again", "further", "then", "once", "here", "there", "where",
        "about", "against", "through", "during", "above", "below",
        "up", "down", "out", "off", "even", "since", "until", "while",
        "accept", "close", "search", "menu", "toggle", "skip", "back", "top",
    }

    for item in schema.content:
        text = _plain_text(item)
        words = re.findall(r"[a-zA-Z]{3,}", text)
        for word in words:
            lower = word.lower()
            if lower not in stop_words and len(lower) > 2:
                word_counts[lower] += 1

    for item in schema.seo:
        if item.evidence_type == "SEO_TITLE" and isinstance(item.value, str):
            words = re.findall(r"[a-zA-Z]{3,}", item.value.lower())
            for word in words:
                if word not in stop_words and len(word) > 2:
                    word_counts[word] += 2

    top_keywords = [word.title() for word, _ in word_counts.most_common(10)]
    if top_keywords:
        lines.append("### Top Keywords")
        lines.append("")
        lines.append(", ".join(top_keywords))
        lines.append("")
    return "\n".join(lines), refs


def _build_content_topics(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Primary Topics section with star ratings."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.content:
        return "\n".join(lines), refs

    topic_counts: Counter[str] = Counter()
    for item in schema.content:
        if item.evidence_type == "CONTENT_HEADING":
            text = _plain_text(item)
            words = text.split()
            if len(words) >= 2:
                topic_counts[" ".join(words[:3]).title()] += 1

    if not topic_counts:
        return "\n".join(lines), refs

    lines.append("### Primary Topics")
    lines.append("")
    max_count = max(topic_counts.values()) if topic_counts else 1
    for topic, count in topic_counts.most_common(8):
        stars = "★" * max(1, round(count / max_count * 5))
        lines.append(f"{stars} {topic}")
    lines.append("")
    return "\n".join(lines), refs


def _build_social_presence_improved(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the improved Social Presence section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.social:
        lines.append("No social profiles were detected during this scan.")
        return "\n".join(lines), refs

    known_platforms = [
        "GitHub", "X", "Facebook", "LinkedIn", "Instagram", "YouTube",
        "Bluesky", "Mastodon", "Threads", "TikTok", "Snapchat", "WhatsApp",
        "Telegram", "Behance", "Dribbble", "Flickr", "Twitch",
    ]
    detected_platforms: set[str] = set()
    platform_urls: dict[str, str] = {}

    for item in schema.social:
        val = item.value
        if isinstance(val, dict):
            platform = str(val.get("platform", "Unknown"))
            url = str(val.get("url", ""))
        else:
            platform = "Unknown"
            url = str(val)
        detected_platforms.add(platform)
        if url:
            platform_urls[platform] = url
        if item.evidence_id:
            refs.append(item.evidence_id)

    rows = []
    for platform in known_platforms:
        detected = "✓" if platform in detected_platforms else "—"
        url = platform_urls.get(platform, "")
        display_platform = f"[{platform}]({url})" if url else platform
        rows.append([display_platform, detected])

    lines.append(table(["Platform", "Detected"], rows))
    return "\n".join(lines), refs


def _build_recommendations_improved(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Executive Recommendations section with priority and impact."""
    lines: list[str] = []
    refs: list[str] = []

    recommendations: list[tuple[str, str, str]] = []
    scan_status, _, limitations = _scan_status(schema)
    is_limited = scan_status in ("limited", "none")

    if is_limited:
        recommendations.append(
            ("Low", "Unable to verify recommendations due to limited scan coverage",
             "Re-scan with fewer restrictions for actionable recommendations")
        )
    else:
        if schema.seo:
            seo_types = {i.evidence_type for i in schema.seo}
            if "OPEN_GRAPH" not in seo_types:
                recommendations.append(
                    ("High", "Add Open Graph metadata",
                     "Richer previews when shared socially")
                )
            if "TWITTER_CARD" not in seo_types:
                recommendations.append(
                    ("High", "Add Twitter Cards",
                     "Better previews when shared on X/Twitter")
                )
            if "STRUCTURED_DATA" not in seo_types:
                recommendations.append(
                    ("Medium", "Implement structured data (JSON-LD)",
                     "Help search engines show rich results")
                )
            if "CANONICAL" not in seo_types:
                recommendations.append(
                    ("Medium", "Add canonical URLs",
                     "Reduce duplicate indexing")
                )
            if "SEO_TITLE" not in seo_types:
                recommendations.append(
                    ("High", "Add page titles",
                     "Essential for search visibility")
                )
            if "META_DESCRIPTION" not in seo_types:
                recommendations.append(
                    ("High", "Add meta descriptions",
                     "Improve click-through rates")
                )

        if not schema.social:
            recommendations.append(
                ("Medium", "Establish social media profiles",
                 "Increase brand visibility and referral traffic")
            )

        if schema.content and len(schema.content) < 5:
            recommendations.append(
                ("Medium", "Increase content volume",
                 "Improve organic search visibility and engagement")
            )

    if not recommendations:
        recommendations.append(
            ("Low", "No specific recommendations from this scan",
             "Continue monitoring performance")
        )

    lines.append(table(["Priority", "Recommendation", "Business Impact"], recommendations))
    return "\n".join(lines), refs


def _build_strengths_improved(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Top Strengths section."""
    strengths: list[str] = []
    refs: list[str] = []

    if schema.seo:
        seo_types = {i.evidence_type for i in schema.seo}
        checks = [
            "SEO_TITLE", "META_DESCRIPTION", "CANONICAL", "ROBOTS",
            "LANGUAGE", "CHARSET", "VIEWPORT", "OPEN_GRAPH", "TWITTER_CARD",
        ]
        passed = sum(1 for c in checks if c in seo_types)
        if passed >= 4:
            strengths.append(
                "Strong on-page SEO signals were detected, improving search visibility"
            )
            seo_refs = [
                i.evidence_id for i in schema.seo
                if i.evidence_type in checks[:passed] and i.evidence_id
            ]
            refs.extend(seo_refs)

    if schema.metadata:
        meta_types = {i.evidence_type for i in schema.metadata}
        if "SITE_NAME" in meta_types:
            strengths.append("Brand identity is clearly defined through metadata")
        if len(meta_types) >= 3:
            strengths.append(
                "A rich metadata profile was detected, supporting SEO and device integration"
            )

    if schema.technology:
        seen_names: set[str] = set()
        unique_count = 0
        for item in schema.technology:
            if isinstance(item.value, dict):
                raw_name = item.value.get("name")
                if isinstance(raw_name, str) and raw_name not in seen_names:
                    seen_names.add(raw_name)
                    unique_count += 1
        if unique_count >= 2:
            strengths.append(
                f"Multiple technologies detected ({unique_count}), indicating a modern stack"
            )

    if schema.content and len(schema.content) >= 5:
        strengths.append(
            "Substantial content was extracted, supporting organic search and engagement"
        )

    if schema.social:
        seen_urls: set[str] = set()
        unique_count = 0
        for item in schema.social:
            if isinstance(item.value, dict):
                url = item.value.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_count += 1
        if unique_count >= 1:
            strengths.append(
                f"Active social presence detected on {unique_count} platform(s)"
            )

    if schema.competitors:
        strengths.append("Competitive references were identified, supporting market positioning")

    top_strengths = strengths[:5]
    lines = bullet_list([f"✓ {s}" for s in top_strengths])
    lines += "\n\n**Business Takeaway**\n"
    if top_strengths:
        first = top_strengths[0].split(" - ")[0].split(" (")[0]
        lines += (
            f"The clearest strength is {first.lower()}. "
            "This gives the website a measurable advantage to build on."
        )
    else:
        lines += (
            "No specific strengths could be confirmed from the evidence collected "
            "in this scan. A broader or less restricted scan may surface additional "
            "strengths."
        )
    return lines, refs


def _build_weaknesses_improved(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Improvement Opportunities section."""
    opportunities: list[tuple[str, str, str]] = []
    refs: list[str] = []

    scan_status, _, limitations = _scan_status(schema)
    is_limited = scan_status in ("limited", "none")
    limitation_note = (
        " This may reflect scan limitations rather than a website gap."
        if is_limited and limitations
        else ""
    )

    if not schema.seo:
        opportunities.append(
            ("High", "No on-page SEO evidence was collected during this scan",
             "Cannot assess search visibility")
        )
    else:
        seo_types = {i.evidence_type for i in schema.seo}
        required = ["SEO_TITLE", "META_DESCRIPTION", "CANONICAL"]
        missing = [r for r in required if r not in seo_types]
        if "SEO_TITLE" in missing:
            opportunities.append(
                ("High", "Page title was not detected",
                 "Essential for search visibility and browser tabs")
            )
        if "META_DESCRIPTION" in missing:
            opportunities.append(
                ("High", "Meta description was not detected",
                 "Influences search click-through rate")
            )
        if "CANONICAL" in missing:
            opportunities.append(
                ("Medium", "Canonical URL was not detected",
                 "Helps search engines consolidate duplicate pages")
            )
        if "OPEN_GRAPH" not in seo_types:
            opportunities.append(
                ("Medium", "Open Graph metadata was not detected",
                 "Richer previews when shared socially")
            )
        if "TWITTER_CARD" not in seo_types:
            opportunities.append(
                ("Medium", "Twitter Cards not detected",
                 "Better previews when shared on X/Twitter")
            )
        if "STRUCTURED_DATA" not in seo_types:
            opportunities.append(
                ("Low", "Structured data was not detected",
                 "Missed opportunity for rich search results")
            )

    if not schema.metadata:
        opportunities.append(
            ("Medium", "No brand metadata was collected during this scan",
             "Limited brand presence in search and devices")
        )
    if not schema.technology:
        opportunities.append(
            ("Low", "No technology evidence was collected during this scan",
             "Cannot assess technical stack")
        )
    if not schema.social:
        opportunities.append(
            ("Medium", "No social profiles were detected during this scan",
             "Limited brand visibility and referral traffic")
        )
    if not schema.content:
        opportunities.append(
            ("Low", "No page content was collected during this scan",
             "Limited organic search potential")
        )

    if is_limited and limitations:
        opportunities = [
            (priority, f"{title}.{limitation_note}", benefit)
            for priority, title, benefit in opportunities
        ]

    lines = table(["Priority", "Improvement Opportunity", "Potential Benefit"], opportunities)
    lines += "\n\n**Business Takeaway**\n"
    if len(opportunities) <= 2:
        lines += (
            "Only minor gaps were identified. Addressing these will further improve "
            "search and social performance."
        )
    else:
        high_priority = sum(1 for o in opportunities if o[0] == "High")
        lines += (
            f"{len(opportunities)} improvement opportunities were identified. "
            f"{high_priority} high-priority item(s) should be addressed "
            "first for the quickest result."
        )
    return lines, refs


def _build_technical_diagnostics(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Technical Diagnostics section."""
    lines: list[str] = []
    refs: list[str] = []

    diagnostics = schema.diagnostics
    if not diagnostics:
        lines.append("No diagnostics available.")
        return "\n".join(lines), refs

    rows: list[list[str]] = []
    for key in (
        "total_evidence_items",
        "seo_items",
        "metadata_items",
        "technology_items",
        "content_items",
        "social_items",
        "competitor_items",
    ):
        if key in diagnostics:
            label = "Technology Signals" if key == "technology_items" else humanize_label(key)
            rows.append([label, str(diagnostics[key])])

    if "build_timestamp" in diagnostics:
        rows.append(["Scan Timestamp", str(diagnostics["build_timestamp"])])
    if "sitemap_pages_found" in diagnostics:
        rows.append(["Sitemap Pages Found", str(diagnostics["sitemap_pages_found"])])

    lines.append(table(["Metric", "Value"], rows))
    if schema.evidence:
        lines.append(
            "*Evidence appendix shows a sample of collected items. "
            "Full evidence is available in the JSON export.*"
        )
    return "\n".join(lines), refs


def _build_evidence_appendix(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Evidence Appendix section."""
    lines: list[str] = []
    refs: list[str] = []

    items = schema.evidence[:20]
    if not items:
        lines.append("No evidence was collected.")
        return "\n".join(lines), refs

    seen_values: set[str] = set()
    diverse_items: list[EvidenceItem] = []
    for item in items:
        value_key = humanize_value(item.value, empty="")
        if value_key not in seen_values:
            seen_values.add(value_key)
            diverse_items.append(item)
        if len(diverse_items) >= 20:
            break

    rows: list[list[str]] = []
    for item in diverse_items:
        evidence_id = item.evidence_id or "N/A"
        evidence_type = humanize_label(item.evidence_type)
        source = humanize_label(item.extractor_source)
        value = humanize_value(item.value, empty="")
        if len(value) > 120:
            value = truncate_text(value, 120)
        rows.append([evidence_id, evidence_type, source, value])
        if item.evidence_id:
            refs.append(item.evidence_id)

    lines.append(table(["ID", "Type", "Source", "Value"], rows))
    lines.append("")
    lines.append(
        f"*Showing {len(diverse_items)} of {len(schema.evidence)} evidence "
        "items. Full evidence is available in the JSON export.*"
    )
    return "\n".join(lines), refs


def _build_footer() -> tuple[str, list[str]]:
    """Build the report footer."""
    lines: list[str] = []
    lines.append(hr())
    lines.append("")
    lines.append("Website Intelligence Report")
    lines.append("")
    lines.append("Generated by AIFME Scout OSS")
    lines.append("")
    lines.append(
        "All findings are derived deterministically from collected evidence. "
        "No AI inference or external services were used to produce this report."
    )
    return "\n".join(lines), []


def _build_template_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build a complete template-based summary from schema evidence."""
    sections_text: list[str] = []
    all_refs: list[str] = []

    section_builders = [
        ("Executive Scorecard", _build_executive_scorecard),
        ("Executive Summary", _build_executive_summary),
        ("Business Snapshot", _build_business_snapshot),
        ("Signal Coverage", _build_health_score),
        ("Website Overview", _build_website_overview),
        ("Scan Limitations", _build_scan_limitations),
        ("SEO Analysis", _build_seo_analysis),
        ("Metadata Analysis", _build_metadata_analysis),
        ("Technology Stack", _build_technology_stack),
        ("Technology Maturity", _build_technology_maturity),
        ("Content Analysis", _build_content_analysis),
        ("Social Presence", _build_social_presence),
        ("Competitive Signals", _build_competitive_signals),
        ("Top Strengths", _build_strengths),
        ("Improvement Opportunities", _build_weaknesses),
        ("Executive Recommendations", _build_recommendations),
        ("Technical Diagnostics", _build_technical_diagnostics),
        ("Evidence Appendix", _build_evidence_appendix),
    ]

    for section_name, builder in section_builders:
        section_text, section_refs = builder(schema)
        if section_text:
            sections_text.append(section(section_name, section_text))
            all_refs.extend(section_refs)

    footer_text, footer_refs = _build_footer()
    if footer_text:
        sections_text.append(footer_text)
        all_refs.extend(footer_refs)

    full_text = "\n".join(
        [
            _build_title(schema),
            "",
            join_sections(sections_text),
        ]
    )
    deduplicated_refs = list(dict.fromkeys(all_refs))
    return full_text, deduplicated_refs


def _summarize_llm(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Attempt LLM-backed summary generation.

    In this milestone LLM mode is not implemented. This function exists as the
    integration point and always falls back to template mode.
    """
    return _build_template_summary(schema)


def summarize(
    schema: ScoutSchema,
    mode: ScanMode = ScanMode.NO_LLM,
) -> Summary:
    """Produce a descriptive evidence-linked summary from a ScoutSchema.

    Every claim in the returned summary traces to one or more Evidence IDs in
    the input schema. No claim is invented or inferred beyond the collected
    evidence.
    """
    if mode == ScanMode.LLM:
        text, evidence_refs = _summarize_llm(schema)
    else:
        text, evidence_refs = _build_template_summary(schema)

    status, status_label, _ = _scan_status(schema)
    _, coverage = _compute_health_score(schema)
    classification, _ = _classify_target(schema)

    return Summary(
        text=text,
        evidence_refs=evidence_refs,
        scan_status=status_label,
        confidence=_scan_confidence(schema, status, coverage),
        scan_coverage=float(coverage),
        target_classification=classification,
    )


def _scan_confidence(schema: ScoutSchema, status: str, coverage: int) -> str:
    """Derive a plain-language confidence label for the scan."""
    _, _, limitations = _scan_status(schema)
    if status == "none":
        return "None"
    if limitations:
        return "Low"
    if coverage >= 90 and status == "complete":
        return "High"
    if coverage >= 70:
        return "Medium"
    return "Low"


def _filter_navigation_noise(text: str) -> bool:
    """Return True if the text should be filtered out as navigation noise."""
    lower = text.lower().strip()
    return lower in _NAVIGATION_NOISE or lower.startswith("back to") or len(lower) <= 2
