"""Summary Builder module.

Produces a deterministic, evidence-linked descriptive summary from a
ScoutSchema. In no-LLM mode the summary is template-based and derives
every claim from collected evidence. In LLM mode the implementation
falls back to the same template-based summary when no provider is
configured; LLM-backed generation is intentionally deferred to keep
this milestone within the frozen Architecture spec.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aifme_scout.exporters.renderers import (
    bullet_list,
    hr,
    join_sections,
    score_bar,
    section,
    status_badge,
    table,
)
from aifme_scout.extractors.models import (
    EvidenceItem,
    ScoutSchema,
)
from aifme_scout.utils.constants import ScanMode
from aifme_scout.utils.models import Summary

if TYPE_CHECKING:
    pass


_VERSION = "1.0.0rc3"
_REPO_URL = "https://github.com/SureshBabuoo7/aifme-scout"
_PYPI_URL = "https://pypi.org/project/aifme-scout/"

_NAVIGATION_NOISE = {
    "back to top", "menu", "reset", "smaller", "larger", "close",
    "skip to content", "aa", "search", "toggle navigation", "toggle menu",
}


def _get_evidence_value(item: EvidenceItem) -> str:
    """Extract a displayable value from an evidence item."""
    value = item.value
    if isinstance(value, dict):
        parts = [f"{k}={v}" for k, v in value.items() if v]
        return ", ".join(parts) if parts else str(value)
    return str(value) if value is not None else ""


def _classify_target(schema: ScoutSchema) -> tuple[str, str]:
    """Classify the target site using only deterministic evidence.

    Returns:
        (classification, evidence_id) tuple.
    """
    tech_names: set[str] = set()
    for item in schema.technology:
        if isinstance(item.value, dict):
            name = item.value.get("name")
            if isinstance(name, str):
                tech_names.add(name.lower())

    content_text_parts: list[str] = []
    for item in schema.content:
        if isinstance(item.value, str):
            content_text_parts.append(item.value.lower())
        elif isinstance(item.value, dict):
            for v in item.value.values():
                if isinstance(v, str):
                    content_text_parts.append(v.lower())
    content_text = " ".join(content_text_parts)

    ecommerce_indicators = {
        "shopify", "woocommerce", "magento", "bigcommerce",
        "stripe", "paypal", "cart", "checkout", "product", "shop",
    }
    saas_indicators = {
        "api", "pricing", "subscription", "trial", "saas", "cloud",
        "dashboard", "signup", "login", "demo",
    }
    blog_indicators = {
        "blog", "article", "post", "author", "category",
        "rss", "wordpress", "medium", "newsletter",
    }
    agency_indicators = {
        "agency", "client", "portfolio", "service", "consulting",
        "case study", "our work", "what we do",
    }
    media_indicators = {
        "video", "podcast", "streaming", "media",
        "channel", "youtube", "watch",
    }
    doc_indicators = {
        "documentation", "docs", "guide", "tutorial", "reference",
        "api reference", "manual", "help center", "knowledge base",
    }
    programming_indicators = {
        "python", "java", "javascript", "ruby", "go", "rust",
        "download", "install", "documentation", "docs",
    }
    corporate_indicators = {
        "about us", "our team", "careers", "contact", "company",
        "investor", "press", "leadership",
    }
    government_indicators = {
        "government", "official", ".gov", "public service",
        "citizen", "policy", "regulation",
    }
    education_indicators = {
        "university", "college", "school", "education", ".edu",
        "course", "student", "faculty", "academic",
    }
    news_indicators = {
        "news", "breaking", "journalist", "editorial",
        "headline", "report", "magazine",
    }

    def _indicator_hits(indicators: set[str], text: str) -> int:
        return sum(1 for ind in indicators if ind in text)

    scores = {
        "e-commerce platform": (
            _indicator_hits(ecommerce_indicators, content_text)
            + sum(1 for t in tech_names if t in ecommerce_indicators)
        ),
        "saas platform": (
            _indicator_hits(saas_indicators, content_text)
            + sum(1 for t in tech_names if t in saas_indicators)
        ),
        "news publisher": (
            _indicator_hits(news_indicators, content_text)
            + sum(1 for t in tech_names if t in news_indicators)
        ),
        "programming language documentation portal": (
            _indicator_hits(programming_indicators, content_text)
            + sum(1 for t in tech_names if t in programming_indicators)
            + (3 if _indicator_hits(doc_indicators, content_text) > 0 else 0)
        ),
        "documentation platform": (
            _indicator_hits(doc_indicators, content_text)
            + sum(1 for t in tech_names if t in doc_indicators)
        ),
        "corporate website": (
            _indicator_hits(corporate_indicators, content_text)
            + sum(1 for t in tech_names if t in corporate_indicators)
        ),
        "government portal": (
            _indicator_hits(government_indicators, content_text)
            + sum(1 for t in tech_names if t in government_indicators)
        ),
        "educational institution": (
            _indicator_hits(education_indicators, content_text)
            + sum(1 for t in tech_names if t in education_indicators)
        ),
    }

    best_category = max(scores, key=lambda k: scores[k])
    if scores[best_category] == 0:
        return ("general website", "")

    evidence_id = ""
    for item in schema.technology:
        if item.evidence_id and best_category in ("e-commerce platform", "saas platform"):
            evidence_id = item.evidence_id
            break

    return (best_category, evidence_id)


def _count_items(schema: ScoutSchema, category: str) -> int:
    """Count evidence items for a given category."""
    return len(getattr(schema, category, []))


def _get_seo_status(item_value: object) -> tuple[str, str]:
    """Return (status_label, detail) for an SEO evidence value."""
    if item_value is None:
        return ("MISSING", "Not found")
    if isinstance(item_value, dict):
        noindex = item_value.get("noindex")
        if noindex is True:
            return ("NOINDEX", "Blocked from indexing")
        if noindex is False:
            return ("INDEXABLE", "Indexable")
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
            return ("PRESENT", "JSON-LD detected")
        return ("PASS", "Detected")
    s = str(item_value)
    if not s:
        return ("MISSING", "Not found")
    return ("PASS", s)


def _compute_health_score(schema: ScoutSchema) -> tuple[list[tuple[str, int]], int]:
    """Compute health scores for each category.

    Returns:
        (scores, overall_score) where scores is a list of
        (category, score_0_100) tuples.
    """
    scores: list[tuple[str, int]] = []
    weights = {
        "Website Reachability": 15,
        "SEO": 20,
        "Metadata": 15,
        "Technology": 20,
        "Content": 20,
        "Social": 10,
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
            "title": any(
                _get_evidence_value(i)
                for i in seo_items
                if i.evidence_type == "SEO_TITLE"
            ),
            "meta_description": any(
                _get_evidence_value(i)
                for i in seo_items
                if i.evidence_type == "META_DESCRIPTION"
            ),
            "canonical": any(
                _get_evidence_value(i)
                for i in seo_items
                if i.evidence_type == "CANONICAL"
            ),
            "charset": any(
                _get_evidence_value(i)
                for i in seo_items
                if i.evidence_type == "CHARSET"
            ),
            "viewport": any(
                _get_evidence_value(i)
                for i in seo_items
                if i.evidence_type == "VIEWPORT"
            ),
            "language": any(
                _get_evidence_value(i)
                for i in seo_items
                if i.evidence_type == "LANGUAGE"
            ),
            "robots": any(
                _get_evidence_value(i)
                for i in seo_items
                if i.evidence_type == "ROBOTS"
            ),
        }
        passed = sum(1 for v in checks.values() if v)
        seo_score = int((passed / len(checks)) * 100) if checks else 0
    scores.append(("SEO", seo_score))
    earned += int(weights["SEO"] * seo_score / 100)

    metadata_items = schema.metadata
    metadata_score = 0
    if metadata_items:
        unique_types = {i.evidence_type for i in metadata_items}
        metadata_score = min(100, len(unique_types) * 15)
    scores.append(("Metadata", metadata_score))
    earned += int(weights["Metadata"] * metadata_score / 100)

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
    scores.append(("Social", social_score))
    earned += int(weights["Social"] * social_score / 100)

    overall = int(earned / total * 100) if total > 0 else 0
    return scores, overall


def _get_website_type(schema: ScoutSchema) -> str:
    classification, _ = _classify_target(schema)
    labels = {
        "e-commerce platform": "E-Commerce Platform",
        "saas platform": "SaaS / Web App",
        "news publisher": "News Publisher",
        "programming language documentation portal": "Programming Language Documentation Portal",
        "documentation platform": "Documentation Platform",
        "corporate website": "Corporate Website",
        "government portal": "Government Portal",
        "educational institution": "Educational Institution",
        "general website": "General Website",
    }
    return labels.get(classification, classification.title())


def _get_responsive(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "VIEWPORT":
            val = item.value
            if val:
                return "Yes"
    for item in schema.content:
        val = _get_evidence_value(item).lower()
        if "viewport" in val and "width=device-width" in val:
            return "Yes"
    return "Unknown"


def _has_jsonld(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "STRUCTURED_DATA":
            val = item.value
            if isinstance(val, dict) and val.get("has_json_ld"):
                return "Present"
            if isinstance(val, str) and "json" in val.lower():
                return "Present"
    return "Absent"


def _has_rss(schema: ScoutSchema) -> str:
    for item in schema.metadata:
        if item.evidence_type in ("RSS_FEED", "ATOM_FEED"):
            return "Available"
    return "Not Available"


def _has_canonical(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "CANONICAL":
            val = item.value
            if val:
                return "Available"
    return "Not Set"


def _get_language(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "LANGUAGE":
            val = item.value
            if isinstance(val, dict):
                raw = val.get("value", "Unknown")
                return raw if isinstance(raw, str) else "Unknown"
            return str(val) if val else "Unknown"
    return "Unknown"


def _get_charset(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "CHARSET":
            val = item.value
            if val:
                return str(val)
    return "Unknown"


def _get_robots_status(schema: ScoutSchema) -> str:
    for item in schema.seo:
        if item.evidence_type == "ROBOTS":
            val = item.value
            if val:
                return str(val)
    return "Not configured"


def _build_executive_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Executive Summary section."""
    lines: list[str] = []
    refs: list[str] = []

    target = schema.site.target_url or schema.site.url
    refs.append(target)
    lines.append(f"**Website:** {target}")

    statuses, confidence = _get_scan_status(schema)
    overall_status = "PASS"
    for _, status, _ in statuses:
        if status in ("MISSING", "FAIL"):
            overall_status = "FAIL"
            break
        if status == "LIMITED":
            overall_status = "LIMITED"

    lines.append(f"**Overall Status:** {status_badge(overall_status)}")
    lines.append(f"**Overall Confidence:** {confidence}")
    lines.append(f"**Evidence Collected:** {len(schema.evidence)}")

    scores, coverage = _compute_health_score(schema)
    lines.append(f"**Overall Coverage:** {coverage}%")

    lines.append("")
    lines.append("**Overall Assessment**")
    lines.append("")

    classification_display = _get_website_type(schema)
    strengths: list[str] = []
    weaknesses: list[str] = []

    for name, status, _ in statuses:
        if status == "PASS":
            strengths.append(name)
        elif status in ("MISSING", "FAIL"):
            weaknesses.append(name)

    summary_parts = []
    summary_parts.append(f"{target} is a {classification_display}.")

    seo_gaps = []
    if schema.seo:
        seo_types = {i.evidence_type for i in schema.seo}
        if "OPEN_GRAPH" not in seo_types:
            seo_gaps.append("Open Graph")
        if "TWITTER_CARD" not in seo_types:
            seo_gaps.append("Twitter Card")

    if overall_status == "FAIL":
        summary_parts.append("The website has critical gaps that need immediate attention.")
    elif overall_status == "LIMITED":
        summary_parts.append("The website has limited data available due to anti-bot protection or access restrictions.")
    elif seo_gaps:
        summary_parts.append("The website demonstrates strong technical implementation and search engine optimization.")
        if len(seo_gaps) == 1:
            summary_parts.append(f"A small number of marketing metadata improvements remain, including {seo_gaps[0]} support.")
        else:
            summary_parts.append(f"A small number of marketing metadata improvements remain, including {', '.join(seo_gaps[:-1])} and {seo_gaps[-1]} support.")
    else:
        summary_parts.append("The website demonstrates strong technical implementation and search engine optimization.")

    summary_parts.append(
        f"This analysis is based on {len(schema.evidence)} collected evidence points "
        f"covering {coverage}% of available signals."
    )

    lines.append(" ".join(summary_parts))

    return "\n".join(lines), refs


def _get_scan_status(schema: ScoutSchema) -> tuple[list[tuple[str, str, str]], str]:
    """Determine scan status for each category.

    Returns:
        (status_list, overall_confidence) where status_list contains
        (category, status, reason) tuples.
    """
    statuses: list[tuple[str, str, str]] = []
    categories = [
        ("SEO", schema.seo, "SEO signals collected"),
        ("Metadata", schema.metadata, "Metadata collected"),
        ("Technology", schema.technology, "Technologies detected"),
        ("Content", schema.content, "Content extracted"),
        ("Social", schema.social, "Social profiles found"),
    ]

    anti_bot_indicators = ["cloudflare", "captcha", "challenge", "access denied", "403", "401"]
    has_anti_bot = False
    for item in schema.content:
        val = _get_evidence_value(item).lower()
        if any(ind in val for ind in anti_bot_indicators):
            has_anti_bot = True
            break
    for item in schema.seo:
        val = _get_evidence_value(item).lower()
        if any(ind in val for ind in anti_bot_indicators):
            has_anti_bot = True
            break

    for name, items, success_msg in categories:
        count = len(items)
        if count > 0:
            statuses.append((name, "PASS", success_msg))
        elif has_anti_bot:
            statuses.append((name, "LIMITED", "Limited by anti-bot protection"))
        else:
            statuses.append((name, "MISSING", "No data found"))

    if has_anti_bot:
        confidence = "Low"
    elif all(s == "PASS" for _, s, _ in statuses):
        confidence = "High"
    elif any(s == "PASS" for _, s, _ in statuses):
        confidence = "Medium"
    else:
        confidence = "Low"

    return statuses, confidence


def _build_health_score(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Health Score section."""
    lines: list[str] = []
    refs: list[str] = []

    scores, overall = _compute_health_score(schema)

    lines.append("| Area | Score |")
    lines.append("|------|-------|")
    for category, score in scores:
        lines.append(f"| {category} | {score_bar(score)} |")

    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    if overall >= 80:
        lines.append("The website is in good shape. Focus on maintaining current strengths.")
    elif overall >= 60:
        lines.append("The website has solid foundations but has clear opportunities for improvement.")
    else:
        lines.append("The website needs attention. Prioritize the weaknesses and recommendations below.")

    return "\n".join(lines), refs


def _build_website_overview(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Website Overview section."""
    lines: list[str] = []
    refs: list[str] = []

    target = schema.site.target_url or schema.site.url
    refs.append(target)

    pairs: list[tuple[str, str]] = [
        ("URL", target),
        ("Website Type", _get_website_type(schema)),
        ("Responsive", _get_responsive(schema)),
        ("Structured Data", _has_jsonld(schema)),
        ("RSS Feeds", _has_rss(schema)),
        ("Canonical URL", _has_canonical(schema)),
        ("Character Encoding", _get_charset(schema)),
        ("Search Engine Instructions", _get_robots_status(schema)),
    ]

    display_pairs: list[tuple[str, str]] = []
    for key, value in pairs:
        if value and value != "Unknown":
            display_pairs.append((key, value))

    if display_pairs:
        lines.append(table(["Item", "Value"], display_pairs))
    else:
        lines.append("No website overview data available.")

    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    if display_pairs:
        lines.append("This overview confirms the website is properly configured for global visitors and search engines.")
    else:
        lines.append("Basic website configuration detected.")

    return "\n".join(lines), refs


def _build_seo_analysis(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the SEO Analysis section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.seo:
        lines.append("No SEO information was collected.")
        lines.append("")
        lines.append("This means search engines may not see the website correctly, "
                      "which can reduce organic traffic.")
        return "\n".join(lines), refs

    seo_checks = [
        ("Page Title", "SEO_TITLE", "The title appears in search results and browser tabs"),
        ("Meta Description", "META_DESCRIPTION", "The description influences click-through rate from search"),
        ("Canonical URL", "CANONICAL", "Prevents duplicate content issues in search"),
        ("Search Engine Instructions", "ROBOTS", "Tells search engines which pages to index"),
        ("Language", "LANGUAGE", "Helps search engines serve the right audience"),
        ("Character Encoding", "CHARSET", "Ensures text displays correctly for all visitors"),
        ("Viewport", "VIEWPORT", "Required for mobile-friendly search ranking"),
    ]

    structured_checks = [
        ("Open Graph", "OPEN_GRAPH", "Controls how pages appear when shared on social media"),
        ("Twitter Card", "TWITTER_CARD", "Controls how pages appear when shared on X/Twitter"),
        ("Structured Data", "STRUCTURED_DATA", "Helps search engines display rich results"),
    ]

    seo_map: dict[str, EvidenceItem] = {}
    for seo_item in schema.seo:
        seo_map[seo_item.evidence_type] = seo_item

    rows: list[list[str]] = []
    for label, evidence_type, impact in seo_checks:
        found = seo_map.get(evidence_type)
        if found is not None:
            status, detail = _get_seo_status(found.value)
            if status == "MISSING":
                status_label = "Not set"
            elif status == "PASS":
                status_label = "Yes"
            else:
                status_label = status_badge(status)
            display_value = detail if len(detail) <= 60 else detail[:57] + "..."
            rows.append([label, status_label, display_value])
            if found.evidence_id:
                refs.append(found.evidence_id)
        else:
            rows.append([label, "Not set", "Not configured"])

    for label, evidence_type, impact in structured_checks:
        found = seo_map.get(evidence_type)
        if found is not None:
            status, detail = _get_seo_status(found.value)
            if status == "MISSING":
                status_label = "Not set"
            elif status == "PASS":
                status_label = "Yes"
            else:
                status_label = status_badge(status)
            display_value = detail if len(detail) <= 60 else detail[:57] + "..."
            rows.append([label, status_label, display_value])
            if found.evidence_id:
                refs.append(found.evidence_id)
        else:
            rows.append([label, "Not set", "Not detected"])

    lines.append(table(["SEO Item", "Status", "Value"], rows))
    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")

    missing = [r[0] for r in rows if r[1] == "Not set"]
    if missing:
        lines.append(f"Missing SEO items: {', '.join(missing)}. "
                      f"These gaps can reduce search visibility and click-through rates.")
    else:
        lines.append("All core SEO elements are present. The website is well-optimized for search engines.")

    return "\n".join(lines), refs


def _build_metadata_analysis(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Metadata Analysis section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.metadata:
        lines.append("No metadata detected.")
        lines.append("")
        lines.append("Missing metadata can hurt search rankings and brand consistency.")
        return "\n".join(lines), refs

    brand_items = []
    favicons: list[str] = []
    rss_feeds: list[str] = []
    verification: list[str] = []

    for item in schema.metadata:
        val = item.value
        if item.evidence_type == "SITE_NAME":
            if val:
                brand_items.append(("Brand", str(val)))
        elif item.evidence_type == "FAVICON":
            if val:
                favicons.append(str(val))
        elif item.evidence_type in ("RSS_FEED", "ATOM_FEED"):
            if val:
                rss_feeds.append(str(val))
        elif item.evidence_type == "VERIFICATION_TAG":
            if isinstance(val, dict):
                platform = val.get("platform", "")
                value = val.get("value", "")
                if platform and value:
                    verification.append(f"{platform.title()}: {value}")
        elif item.evidence_type == "GENERATOR" and val:
            brand_items.append(("Generator", str(val)))
        elif item.evidence_type == "AUTHOR" and val:
            brand_items.append(("Author", str(val)))
        elif item.evidence_type == "PUBLISHER" and val:
            brand_items.append(("Publisher", str(val)))

    if brand_items:
        lines.append("**Brand**")
        lines.append("")
        for key, value in brand_items:
            lines.append(f"- {key}: {value}")
        lines.append("")

    if favicons:
        lines.append("**Brand Icon**")
        lines.append("")
        lines.append("Brand icon detected.")
        lines.append("")

    if rss_feeds:
        lines.append("**RSS Feeds**")
        lines.append("")
        lines.append(bullet_list(rss_feeds[:5]))
        lines.append("")

    if verification:
        lines.append("**Verification**")
        lines.append("")
        lines.append(bullet_list(verification[:5]))
        lines.append("")

    lines.append("**Business Takeaway**")
    lines.append("")
    parts = []
    if brand_items:
        parts.append("the site has a defined brand identity")
    if favicons:
        parts.append("bookmark icons are set up")
    if rss_feeds:
        parts.append("content can be syndicated automatically")
    if verification:
        parts.append("search engine verification is configured")

    if parts:
        lines.append(f"Metadata shows {', '.join(parts)}.")
    else:
        lines.append("Limited metadata detected. More metadata can improve search appearance.")

    return "\n".join(lines), refs


def _build_technology_stack(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Technology Stack section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.technology:
        lines.append("No technologies detected.")
        lines.append("")
        lines.append("Technology detection helps understand the site's infrastructure and potential vulnerabilities.")
        return "\n".join(lines), refs

    category_explanations = {
        "frontend": "user interface technology",
        "backend": "server-side technology",
        "cms": "content management system",
        "e-commerce": "online store platform",
        "analytics": "traffic tracking tool",
        "language": "programming language",
        "framework": "development framework",
        "web-server": "web server software",
        "hosting": "hosting provider",
    }

    seen: set[tuple[str, str]] = set()
    rows: list[list[str]] = []
    for item in schema.technology:
        val = item.value
        if isinstance(val, dict):
            raw_name = val.get("name", "Unknown")
            raw_category = val.get("category", "Unknown")
            raw_confidence = val.get("confidence", "medium")
            raw_detection = val.get("detection_method", "fingerprint")
            name = raw_name if isinstance(raw_name, str) else str(raw_name)
            category = raw_category if isinstance(raw_category, str) else str(raw_category)
            confidence = raw_confidence if isinstance(raw_confidence, str) else str(raw_confidence)
            detection = raw_detection if isinstance(raw_detection, str) else str(raw_detection)
        else:
            name = str(val)
            category = "Unknown"
            confidence = "medium"
            detection = "fingerprint"

        key = (name.lower(), category.lower())
        if key in seen:
            continue
        seen.add(key)

        readable_category = category_explanations.get(category.lower(), category)
        readable_detection = "Automated detection" if detection == "fingerprint" else detection
        rows.append([name, readable_category, status_badge(confidence), readable_detection])
        if item.evidence_id:
            refs.append(item.evidence_id)

    rows.sort(key=lambda r: r[0].lower())
    lines.append(table(["Technology", "Category", "Confidence", "Detection"], rows))
    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    if rows:
        lines.append(f"The site runs on {', '.join(r[0] for r in rows[:3])}. "
                      "This stack is modern and widely supported, reducing technical risk.")
    else:
        lines.append("No technology detected. This limits the ability to assess infrastructure quality.")

    return "\n".join(lines), refs


def _filter_navigation_noise(text: str) -> bool:
    """Return True if the text should be filtered out as navigation noise."""
    lower = text.lower().strip()
    return lower in _NAVIGATION_NOISE or lower.startswith("back to") or len(lower) <= 2


def _build_content_analysis(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Content Analysis section."""
    lines: list[str] = []
    refs: list[str] = []

    content_items = schema.content
    if not content_items:
        lines.append("No content was extracted.")
        lines.append("")
        lines.append("This limits the analysis. JavaScript-heavy sites may need a different scanner.")
        return "\n".join(lines), refs

    headings: list[tuple[int, str]] = []
    topics: list[str] = []
    seen_headings: set[str] = set()

    for item in content_items:
        val = _get_evidence_value(item)
        if item.evidence_type == "CONTENT_HEADING":
            if "level=" in val and "text=" in val:
                parts = dict(part.split("=", 1) for part in val.split(", ") if "=" in part)
                level_str = parts.get("level", "")
                text = parts.get("text", val)
                if level_str.isdigit():
                    level = int(level_str)
                    if not _filter_navigation_noise(text) and text not in seen_headings:
                        seen_headings.add(text)
                        headings.append((level, text))
            else:
                if not _filter_navigation_noise(val) and val not in seen_headings:
                    seen_headings.add(val)
                    headings.append((2, val))
        elif item.evidence_type == "CONTENT_PARAGRAPH":
            words = val.split()
            if len(words) > 5:
                topics.append(val[:100])

    if topics:
        lines.append("**Main Topics**")
        lines.append("")
        unique_topics = list(dict.fromkeys(topics))[:8]
        lines.append(bullet_list(unique_topics))
        lines.append("")

    if headings:
        lines.append("**Headings**")
        lines.append("")
        for level, text in headings[:15]:
            prefix = "#" * min(level, 3)
            lines.append(f"- {prefix} {text}")
        if len(headings) > 15:
            lines.append(f"- ... and {len(headings) - 15} more")
        lines.append("")

    lines.append("**Business Takeaway**")
    lines.append("")
    if headings:
        main_topic = headings[0][1]
        other_headings = [h[1] for h in headings[1:3]]
        if other_headings:
            lines.append(f"The page covers {', '.join(other_headings)}. "
                          "Clear headings help visitors and search engines understand the content.")
        else:
            lines.append(f"The page focuses on \"{main_topic}\". "
                          "Clear headings help visitors and search engines understand the content.")
    else:
        lines.append("Content structure is limited. More structured content can improve engagement.")

    return "\n".join(lines), refs


def _build_social_presence(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Social Presence section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.social:
        lines.append("No social profiles detected.")
        lines.append("")
        lines.append("Without social profiles, the brand misses opportunities for engagement and traffic.")
        return "\n".join(lines), refs

    seen: set[str] = set()
    rows: list[list[str]] = []
    for item in schema.social:
        val = item.value
        if isinstance(val, dict):
            platform = val.get("platform", "Unknown")
            url = val.get("url", "")
            username = val.get("username", "")
        else:
            platform = "Unknown"
            url = str(val)
            username = ""

        account = username or url
        if url not in seen and url:
            seen.add(url)
            rows.append([platform, account])
            if item.evidence_id:
                refs.append(item.evidence_id)

    if len(rows) == 1:
        lines.append(f"**{rows[0][0]}:** {rows[0][1]}")
    elif rows:
        lines.append(table(["Platform", "Account"], rows))
    else:
        lines.append("No social profiles detected.")

    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    lines.append("Social profiles help build brand trust and drive referral traffic. "
                  "Consider adding more platforms to reach a wider audience.")

    return "\n".join(lines), refs


def _build_competitive_signals(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Competitive Signals section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.competitors:
        lines.append("No competitor signals detected.")
        lines.append("")
        lines.append("Without competitor data, it is harder to benchmark performance and identify gaps.")
        return "\n".join(lines), refs

    seen: set[str] = set()
    rows: list[list[str]] = []
    for item in schema.competitors:
        val = item.value
        if isinstance(val, dict):
            name = val.get("name", "Unknown")
            url = val.get("url", "") or ""
        else:
            name = str(val)
            url = ""

        if name not in seen:
            seen.add(name)
            rows.append([name, url if url else "N/A"])
            if item.evidence_id:
                refs.append(item.evidence_id)

    if len(rows) == 1:
        lines.append(f"**Competitor:** {rows[0][0]}")
        if rows[0][1] != "N/A":
            lines.append(f"**URL:** {rows[0][1]}")
    elif rows:
        lines.append(table(["Competitor", "URL"], rows))
    else:
        lines.append("No competitor signals detected.")

    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    if len(rows) == 1:
        lines.append(f"Competitor awareness helps the business stay competitive. "
                      f"Currently {len(rows)} competitor identified for further analysis.")
    else:
        lines.append(f"Competitor awareness helps the business stay competitive. "
                      f"Currently {len(rows)} competitors identified for further analysis.")

    return "\n".join(lines), refs


def _build_strengths(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Strengths section."""
    strengths: list[str] = []
    refs: list[str] = []

    if schema.seo:
        seo_types = {i.evidence_type for i in schema.seo}
        checks = ["SEO_TITLE", "META_DESCRIPTION", "CANONICAL", "ROBOTS", "LANGUAGE", "CHARSET"]
        passed = sum(1 for c in checks if c in seo_types)
        if passed >= 4:
            strengths.append("Strong SEO implementation - the site is optimized for search engines")
            seo_refs = [
                i.evidence_id
                for i in schema.seo
                if i.evidence_type in checks[:passed] and i.evidence_id
            ]
            refs.extend(seo_refs)

    if schema.metadata:
        meta_types = {i.evidence_type for i in schema.metadata}
        if "SITE_NAME" in meta_types:
            strengths.append("Rich structured metadata - search engines understand the brand")
        if len(meta_types) >= 3:
            strengths.append("Comprehensive metadata profile - strong foundation for SEO")

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
            strengths.append("Modern web infrastructure - reliable and scalable technology")

    if schema.content and len(schema.content) >= 5:
        strengths.append("Large content footprint - good for organic search and engagement")

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
            strengths.append("Active social presence - brand is visible on social platforms")

    if schema.competitors:
        strengths.append("Competitive awareness - market positioning is being tracked")

    if not strengths:
        strengths.append("No specific strengths detected from current evidence")

    lines = bullet_list(strengths)
    lines += "\n\n**Business Takeaway**\n"
    if strengths:
        first_strength = strengths[0].split(" - ")[0]
        lines += f"The biggest strength is {first_strength}. This gives the website a competitive advantage."
    else:
        lines += "No clear strengths detected. Focus on building foundational SEO and content."

    return lines, refs


def _build_weaknesses(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Weaknesses section."""
    weaknesses: list[str] = []
    refs: list[str] = []

    if not schema.seo:
        weaknesses.append("No SEO signals detected - the site may be invisible to search engines")
    else:
        seo_types = {i.evidence_type for i in schema.seo}
        required = ["SEO_TITLE", "META_DESCRIPTION", "CANONICAL"]
        missing = [r for r in required if r not in seo_types]
        if "SEO_TITLE" in missing:
            weaknesses.append("Missing page title - reduces search visibility and click-through rate")
        if "META_DESCRIPTION" in missing:
            weaknesses.append("Missing meta description - reduces click-through rate from search")
        if "CANONICAL" in missing:
            weaknesses.append("Missing canonical URL - risks duplicate content penalties")

    if not schema.metadata:
        weaknesses.append("No metadata detected - weak brand presence in search results")

    if not schema.technology:
        weaknesses.append("No technology stack identified - infrastructure is unknown")

    if not schema.social:
        weaknesses.append("No social profiles detected - missed opportunities for engagement and traffic")

    if schema.seo:
        seo_types = {i.evidence_type for i in schema.seo}
        if "OPEN_GRAPH" not in seo_types:
            weaknesses.append("Missing Open Graph - pages show poor previews when shared on social media")
        if "TWITTER_CARD" not in seo_types:
            weaknesses.append("Missing Twitter Cards - reduced engagement when shared on X/Twitter")

    if not weaknesses:
        weaknesses.append("No weaknesses detected from current evidence")

    lines = bullet_list(weaknesses)
    lines += "\n\n**Business Takeaway**\n"
    if len(weaknesses) <= 2:
        lines += "Minor gaps identified. Addressing these will improve search and social performance."
    else:
        lines += f"{len(weaknesses)} gaps identified. Prioritize the first two for quickest impact."

    return lines, refs


def _build_recommendations(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Recommendations section."""
    recommendations: list[str] = []
    refs: list[str] = []

    if schema.seo:
        seo_types = {i.evidence_type for i in schema.seo}
        if "OPEN_GRAPH" not in seo_types:
            recommendations.append("Add Open Graph metadata so pages display richer previews when shared on social platforms")
        if "TWITTER_CARD" not in seo_types:
            recommendations.append("Add Twitter Cards metadata to improve engagement when shared on X/Twitter")
        if "STRUCTURED_DATA" not in seo_types:
            recommendations.append("Implement structured data (JSON-LD) to help search engines display rich results")

    if schema.technology:
        seen_names: set[str] = set()
        has_cms = False
        for item in schema.technology:
            if isinstance(item.value, dict):
                raw_name = item.value.get("name", "")
                if isinstance(raw_name, str):
                    name = raw_name.lower()
                    if name and name not in seen_names:
                        seen_names.add(name)
                        if name in {"wordpress", "drupal", "joomla"}:
                            has_cms = True
        if not has_cms and len(seen_names) < 2:
            recommendations.append("Consider adopting a modern CMS to simplify content updates and SEO management")

    if not schema.social:
        recommendations.append("Establish social media profiles to increase brand visibility and drive referral traffic")

    if schema.content and len(schema.content) < 5:
        recommendations.append("Increase content volume to improve organic search visibility and user engagement")

    if not recommendations:
        recommendations.append("No specific recommendations at this time. Continue monitoring performance.")

    lines = bullet_list(recommendations)
    lines += "\n\n**Business Takeaway**\n"
    lines += "These recommendations are prioritized by impact. Start with the first item for quickest results."

    return lines, refs


def _build_diagnostics(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Diagnostics section."""
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
            label = key.replace("_", " ").title()
            rows.append([label, str(diagnostics[key])])

    if "build_timestamp" in diagnostics:
        rows.append(["Scan Timestamp", str(diagnostics["build_timestamp"])])

    lines.append(table(["Metric", "Value"], rows))
    lines.append("")
    lines.append("**Business Takeaway**")
    lines.append("")
    lines.append("These metrics show how much data was collected during the scan. "
                  "Higher counts mean more data was available for analysis.")

    return "\n".join(lines), refs


def _build_evidence_appendix(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Evidence Appendix section."""
    lines: list[str] = []
    refs: list[str] = []

    items = schema.evidence[:20]
    if not items:
        lines.append("No evidence collected.")
        return "\n".join(lines), refs

    rows: list[list[str]] = []
    for item in items:
        evidence_id = item.evidence_id or "N/A"
        evidence_type = item.evidence_type
        source = item.extractor_source
        value = _get_evidence_value(item)
        if len(value) > 80:
            value = value[:77] + "..."
        rows.append([evidence_id, evidence_type, source, value])
        if item.evidence_id:
            refs.append(item.evidence_id)

    lines.append(table(["ID", "Type", "Source", "Value"], rows))
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
    lines.append("For advanced marketing intelligence and strategic recommendations, explore the AIFME Platform.")
    return "\n".join(lines), []


def _build_template_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build a complete template-based summary from schema evidence.

    Returns:
        (text, evidence_refs) tuple.
    """
    sections_text: list[str] = []
    all_refs: list[str] = []

    section_builders = [
        ("Executive Summary", _build_executive_summary),
        ("Health Score", _build_health_score),
        ("Website Overview", _build_website_overview),
        ("SEO Analysis", _build_seo_analysis),
        ("Metadata Analysis", _build_metadata_analysis),
        ("Technology Stack", _build_technology_stack),
        ("Content Analysis", _build_content_analysis),
        ("Social Presence", _build_social_presence),
        ("Competitive Signals", _build_competitive_signals),
        ("Strengths", _build_strengths),
        ("Weaknesses", _build_weaknesses),
        ("Recommendations", _build_recommendations),
        ("Diagnostics", _build_diagnostics),
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

    full_text = join_sections(sections_text)
    deduplicated_refs = list(dict.fromkeys(all_refs))

    return full_text, deduplicated_refs


def _summarize_llm(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Attempt LLM-backed summary generation.

    In this milestone LLM mode is not implemented. This function exists
    as the integration point and always falls back to template mode.
    """
    return _build_template_summary(schema)


def summarize(
    schema: ScoutSchema,
    mode: ScanMode = ScanMode.NO_LLM,
) -> Summary:
    """Produce a descriptive evidence-linked summary from a ScoutSchema.

    Every claim in the returned summary traces to one or more Evidence
    IDs in the input schema. No claim is invented or inferred beyond
    the collected evidence.

    Args:
        schema: The assembled ScoutSchema from the Schema Builder.
        mode: Summary generation mode. ``no-llm`` produces a
            deterministic template-based summary. ``llm`` falls back
            to the same template summary when no provider is available.

    Returns:
        Summary with text and evidence references.
    """
    if mode == ScanMode.LLM:
        text, evidence_refs = _summarize_llm(schema)
    else:
        text, evidence_refs = _build_template_summary(schema)

    return Summary(text=text, evidence_refs=evidence_refs)
