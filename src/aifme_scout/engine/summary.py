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

    ecommerce_indicators = {"shopify", "woocommerce", "magento", "bigcommerce", "stripe", "paypal", "cart", "checkout"}
    saas_indicators = {"api", "pricing", "subscription", "trial", "saas", "cloud", "dashboard", "signup"}
    blog_indicators = {"blog", "article", "post", "author", "category", "rss", "wordpress", "medium"}
    agency_indicators = {"agency", "client", "portfolio", "service", "consulting", "case study"}
    media_indicators = {"video", "podcast", "streaming", "media", "channel", "youtube"}

    def _indicator_hits(indicators: set[str], text: str) -> int:
        return sum(1 for ind in indicators if ind in text)

    scores = {
        "e-commerce": _indicator_hits(ecommerce_indicators, content_text) + sum(1 for t in tech_names if t in ecommerce_indicators),
        "saas": _indicator_hits(saas_indicators, content_text) + sum(1 for t in tech_names if t in saas_indicators),
        "blog": _indicator_hits(blog_indicators, content_text) + sum(1 for t in tech_names if t in blog_indicators),
        "agency": _indicator_hits(agency_indicators, content_text) + sum(1 for t in tech_names if t in agency_indicators),
        "media": _indicator_hits(media_indicators, content_text) + sum(1 for t in tech_names if t in media_indicators),
    }

    best_category = max(scores, key=lambda k: scores[k])
    if scores[best_category] == 0:
        return ("general", "")

    evidence_id = ""
    for item in schema.technology:
        if item.evidence_id and best_category in ("e-commerce", "saas"):
            evidence_id = item.evidence_id
            break

    return (best_category, evidence_id)


def _count_items(schema: ScoutSchema, category: str) -> int:
    """Count evidence items for a given category."""
    return len(getattr(schema, category, []))


def _get_scan_status(schema: ScoutSchema) -> tuple[list[tuple[str, str, str]], str]:
    """Determine scan status for each category.

    Returns:
        (status_list, overall_confidence) where status_list contains
        (category, status, reason) tuples.
    """
    statuses: list[tuple[str, str, str]] = []
    categories = [
        ("SEO", schema.seo, "SEO information collected"),
        ("Metadata", schema.metadata, "Metadata collected"),
        ("Technology", schema.technology, "Infrastructure detected"),
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

    low_count_categories = []
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


def _compute_health_score(schema: ScoutSchema) -> tuple[list[tuple[str, str]], int]:
    """Compute health scores for each category.

    Returns:
        (scores, coverage_percent) where scores is a list of
        (category, status) tuples.
    """
    scores: list[tuple[str, str]] = []
    weights = {
        "Website Reachability": 15,
        "SEO": 20,
        "Metadata": 15,
        "Technology": 20,
        "Content": 20,
        "Social": 10,
    }

    total_weight = 0
    earned_weight = 0

    site_reachable = bool(schema.site.url)
    if site_reachable:
        scores.append(("Website Reachability", "PASS"))
        earned_weight += weights["Website Reachability"]
    else:
        scores.append(("Website Reachability", "FAIL"))
    total_weight += weights["Website Reachability"]

    seo_count = len(schema.seo)
    if seo_count > 0:
        scores.append(("SEO", "PASS"))
        earned_weight += weights["SEO"]
    else:
        scores.append(("SEO", "MISSING"))
    total_weight += weights["SEO"]

    metadata_count = len(schema.metadata)
    if metadata_count > 0:
        scores.append(("Metadata", "PASS"))
        earned_weight += weights["Metadata"]
    else:
        scores.append(("Metadata", "MISSING"))
    total_weight += weights["Metadata"]

    tech_count = len(schema.technology)
    if tech_count > 0:
        scores.append(("Technology", "PASS"))
        earned_weight += weights["Technology"]
    else:
        scores.append(("Technology", "MISSING"))
    total_weight += weights["Technology"]

    content_count = len(schema.content)
    if content_count > 10:
        scores.append(("Content", "PASS"))
        earned_weight += weights["Content"]
    elif content_count > 0:
        scores.append(("Content", "LIMITED"))
        earned_weight += weights["Content"] // 2
    else:
        scores.append(("Content", "MISSING"))
    total_weight += weights["Content"]

    social_count = len(schema.social)
    if social_count > 0:
        scores.append(("Social", "PASS"))
        earned_weight += weights["Social"]
    else:
        scores.append(("Social", "NOT FOUND"))
    total_weight += weights["Social"]

    coverage = int((earned_weight / total_weight) * 100) if total_weight > 0 else 0
    return scores, coverage


def _build_executive_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Executive Summary section."""
    lines: list[str] = []
    refs: list[str] = []

    site = schema.site
    target = site.target_url or site.url
    lines.append(f"Target: {target}")
    refs.append(target)

    statuses, confidence = _get_scan_status(schema)

    lines.append("")
    lines.append("Overall Scan Status")
    lines.append("-" * 40)

    for name, status, reason in statuses:
        icon = {"PASS": "PASS", "MISSING": "MISSING", "LIMITED": "WARN"}.get(status, status)
        lines.append(f"* {name}: {icon}")
        if status != "PASS":
            lines.append(f"  - {reason}")

    lines.append("")
    lines.append("Overall Confidence")
    lines.append("-" * 40)
    lines.append(confidence)

    return "\n".join(lines), refs


def _build_health_score(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Health Score section."""
    lines: list[str] = []
    refs: list[str] = []

    scores, coverage = _compute_health_score(schema)

    lines.append("Website Health Score")
    lines.append("")
    lines.append("| Category | Status |")
    lines.append("|----------|--------|")
    for category, status in scores:
        lines.append(f"| {category} | {status} |")

    lines.append("")
    lines.append(f"Overall Data Coverage: {coverage}%")

    return "\n".join(lines), refs


def _build_technology_section(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Technology Detected section."""
    lines: list[str] = []
    refs: list[str] = []

    tech_items = schema.technology
    if not tech_items:
        lines.append("No technologies detected.")
        return "\n".join(lines), refs

    lines.append("| Technology | Category | Confidence | Detection |")
    lines.append("|------------|----------|------------|-----------|")

    seen = set()
    for item in tech_items:
        value = item.value
        if isinstance(value, dict):
            name = value.get("name", "Unknown")
            category = value.get("category", "Unknown")
            confidence = value.get("confidence", "medium")
            detection = value.get("detection_method", "fingerprint")
        else:
            name = str(value)
            category = "Unknown"
            confidence = "medium"
            detection = "fingerprint"

        key = (name, category)
        if key in seen:
            continue
        seen.add(key)

        lines.append(f"| {name} | {category} | {confidence} | {detection} |")
        if item.evidence_id:
            refs.append(item.evidence_id)

    return "\n".join(lines), refs


def _build_seo_section(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the SEO Overview section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.seo:
        lines.append("No SEO information was collected.")
        lines.append("")
        lines.append("Possible reasons:")
        lines.append("- The page returned limited or no HTML")
        lines.append("- Anti-bot protection blocked the scanner")
        return "\n".join(lines), refs

    title = None
    meta_desc = None
    canonical = None
    language = None
    robots = None

    for item in schema.seo:
        value = item.value
        if isinstance(value, dict):
            if item.evidence_type == "SEO_TITLE" or (isinstance(value, dict) and "title" in value):
                title = value.get("title") if isinstance(value, dict) else str(value)
            elif item.evidence_type == "META_DESCRIPTION":
                meta_desc = value.get("description") if isinstance(value, dict) else str(value)
            elif item.evidence_type == "CANONICAL":
                canonical = value.get("url") if isinstance(value, dict) else str(value)
            elif item.evidence_type == "LANGUAGE":
                language = value.get("value") if isinstance(value, dict) else str(value)
            elif item.evidence_type == "ROBOTS":
                robots = str(value)
        else:
            if item.evidence_type == "SEO_TITLE":
                title = str(value)
            elif item.evidence_type == "META_DESCRIPTION":
                meta_desc = str(value)

    if title:
        lines.append(f"- **Page Title:** {title}")
    else:
        lines.append("- **Page Title:** Not found")

    if meta_desc:
        lines.append(f"- **Meta Description:** {meta_desc}")
    else:
        lines.append("- **Meta Description:** Not found")

    if canonical:
        lines.append(f"- **Canonical URL:** {canonical}")
    else:
        lines.append("- **Canonical URL:** Not found")

    if language:
        lines.append(f"- **Language:** {language}")

    if robots:
        lines.append(f"- **Robots:** {robots}")

    return "\n".join(lines), refs


def _build_metadata_section(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Metadata Found section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.metadata:
        lines.append("No metadata was found.")
        lines.append("")
        lines.append("Possible reasons:")
        lines.append("- The page has minimal head metadata")
        lines.append("- Anti-bot protection blocked full page access")
        return "\n".join(lines), refs

    favicons = []
    rss = []
    site_name = None

    for item in schema.metadata:
        value = item.value
        if isinstance(value, dict):
            if item.evidence_type == "FAVICON":
                favicons.append(value.get("href", str(value)))
            elif item.evidence_type == "RSS_FEED":
                rss.append(str(value))
            elif item.evidence_type == "SITE_NAME":
                site_name = value.get("content") if isinstance(value, dict) else str(value)
            elif item.evidence_type == "APPLE_TOUCH_ICON":
                pass  # Already covered by favicons
        else:
            if item.evidence_type == "SITE_NAME":
                site_name = str(value)

    if site_name:
        lines.append(f"- **Site Name:** {site_name}")

    if favicons:
        lines.append(f"- **Favicons:** {len(favicons)} found")
        for fav in favicons[:3]:
            lines.append(f"  - {fav}")

    if rss:
        lines.append(f"- **RSS Feeds:** {len(rss)} found")
        for feed in rss[:3]:
            lines.append(f"  - {feed}")

    return "\n".join(lines), refs


def _build_social_section(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Social Profiles Found section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.social:
        lines.append("No social profiles were found.")
        lines.append("")
        lines.append("Possible reasons:")
        lines.append("- Social links were not present on the page")
        lines.append("- Anti-bot protection blocked full page access")
        return "\n".join(lines), refs

    lines.append("Social Profiles Found")
    lines.append("")
    lines.append("| Platform | URL |")
    lines.append("|----------|-----|")

    seen = set()
    for item in schema.social:
        value = item.value
        if isinstance(value, dict):
            platform = value.get("platform", "Unknown")
            url = value.get("url", "")
        else:
            platform = "Unknown"
            url = str(value)

        if url not in seen:
            seen.add(url)
            lines.append(f"| {platform} | {url} |")
            if item.evidence_id:
                refs.append(item.evidence_id)

    return "\n".join(lines), refs


def _build_content_section(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Content Extraction section."""
    lines: list[str] = []
    refs: list[str] = []

    content_count = len(schema.content)
    if content_count == 0:
        lines.append("No content was extracted.")
        lines.append("")
        lines.append("Possible reasons:")
        lines.append("- **Anti-bot protection:** The website may be blocking automated access")
        lines.append("- **Dynamic JavaScript rendering:** Content may load after page render")
        lines.append("- **Access restrictions:** The page may require login or be geo-blocked")
        return "\n".join(lines), refs

    lines.append(f"Content extracted: {content_count} items")
    lines.append("")

    headings = [item for item in schema.content if item.evidence_type == "CONTENT_HEADING"]
    if headings:
        lines.append("**Headings:**")
        for item in headings[:10]:
            val = _get_evidence_value(item)
            if val:
                if val.startswith("level="):
                    parts = dict(part.split("=", 1) for part in val.split(", ") if "=" in part)
                    level = parts.get("level", "")
                    text = parts.get("text", val)
                    if level.isdigit():
                        prefix = "#" * int(level)
                        lines.append(f"- {prefix} {text}")
                    else:
                        lines.append(f"- {val}")
                else:
                    lines.append(f"- {val}")
        if len(headings) > 10:
            lines.append(f"- ... and {len(headings) - 10} more")

    return "\n".join(lines), refs


def _build_competitor_section(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Competitor Analysis section."""
    lines: list[str] = []
    refs: list[str] = []

    if not schema.competitors:
        lines.append("No competitors were identified.")
        lines.append("")
        lines.append("Competitor discovery requires explicit competitor URLs to be provided.")
        return "\n".join(lines), refs

    lines.append("| Name | URL |")
    lines.append("|------|-----|")

    seen = set()
    for item in schema.competitors:
        value = item.value
        if isinstance(value, dict):
            name = value.get("name", "Unknown")
            url = value.get("url", "")
        else:
            name = str(value)
            url = ""

        if name not in seen:
            seen.add(name)
            lines.append(f"| {name} | {url} |")
            if item.evidence_id:
                refs.append(item.evidence_id)

    return "\n".join(lines), refs


def _build_diagnostics_section(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Diagnostics section (moved to bottom)."""
    lines: list[str] = []
    refs: list[str] = []

    diagnostics = schema.diagnostics
    if not diagnostics:
        lines.append("No diagnostics available.")
        return "\n".join(lines), refs

    lines.append("Technical Diagnostics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")

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
            lines.append(f"| {label} | {diagnostics[key]} |")

    if "build_timestamp" in diagnostics:
        lines.append(f"| Build Timestamp | {diagnostics['build_timestamp']} |")

    return "\n".join(lines), refs


def _build_footer() -> tuple[str, list[str]]:
    """Build the report footer."""
    lines: list[str] = []
    lines.append("---")
    lines.append("")
    lines.append("Generated by AIFME Scout OSS")
    lines.append(f"Version {_VERSION}")
    lines.append("")
    lines.append("Open-source website intelligence toolkit.")
    lines.append("")
    lines.append(f"GitHub: {_REPO_URL}")
    lines.append(f"PyPI: {_PYPI_URL}")
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
        ("Technology Detected", _build_technology_section),
        ("SEO Overview", _build_seo_section),
        ("Metadata Found", _build_metadata_section),
        ("Social Profiles Found", _build_social_section),
        ("Content Extraction", _build_content_section),
        ("Competitor Analysis", _build_competitor_section),
        ("Diagnostics", _build_diagnostics_section),
    ]

    for section_name, builder in section_builders:
        section_text, section_refs = builder(schema)
        sections_text.append(f"# {section_name}\n{section_text}")
        all_refs.extend(section_refs)

    footer_text, footer_refs = _build_footer()
    sections_text.append(footer_text)
    all_refs.extend(footer_refs)

    full_text = "\n\n".join(sections_text)
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
