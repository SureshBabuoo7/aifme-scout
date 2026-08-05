"""Reusable Markdown renderers for the Website Intelligence Report.

Each helper produces a deterministic, self-contained Markdown fragment.
No AI, no inference, no invented facts - only deterministic transformations
of collected evidence.

These helpers are presentation-only. They never add, remove, or reinterpret
evidence; they format values that were already collected.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

_ELLIPSIS = "\u2026"

#: Tokens that should be rendered in their conventional upper-case form.
_ACRONYMS = {
    "amp": "AMP",
    "api": "API",
    "atom": "Atom",
    "cdn": "CDN",
    "cms": "CMS",
    "crm": "CRM",
    "csp": "CSP",
    "css": "CSS",
    "dns": "DNS",
    "faq": "FAQ",
    "hsts": "HSTS",
    "html": "HTML",
    "http": "HTTP",
    "https": "HTTPS",
    "id": "ID",
    "ip": "IP",
    "js": "JS",
    "json": "JSON",
    "ld": "LD",
    "og": "OG",
    "pwa": "PWA",
    "rdfa": "RDFa",
    "rss": "RSS",
    "saas": "SaaS",
    "seo": "SEO",
    "sms": "SMS",
    "ssl": "SSL",
    "svg": "SVG",
    "tls": "TLS",
    "ui": "UI",
    "uri": "URI",
    "url": "URL",
    "urls": "URLs",
    "utf": "UTF",
    "ux": "UX",
    "xml": "XML",
}

#: Full-key overrides applied before per-word humanisation.
_LABEL_OVERRIDES = {
    "alt": "Alt Text",
    "amp_detection": "AMP",
    "apple_touch_icon": "Apple Touch Icon",
    "detection_method": "Detection Method",
    "dom_path": "DOM Path",
    "has_json_ld": "JSON-LD",
    "has_microdata": "Microdata",
    "has_rdfa": "RDFa",
    "href": "Link",
    "input_names": "Form Fields",
    "list_type": "List Type",
    "meta_description": "Meta Description",
    "msapplication_config": "MS Application Config",
    "msapplication_tileimage": "MS Application Tile Image",
    "noarchive": "No Archive",
    "nofollow": "No Follow",
    "noindex": "No Index",
    "nosnippet": "No Snippet",
    "open_graph": "Open Graph",
    "open_graph_image": "Open Graph Image",
    "open_graph_site_name": "Open Graph Site Name",
    "open_graph_type": "Open Graph Type",
    "open_graph_url": "Open Graph URL",
    "page_url": "Page URL",
    "schema_org_type": "Schema.org Type",
    "seo_title": "Page Title",
    "src": "Source",
    "twitter_card": "Twitter Card",
    "twitter_card_image": "Twitter Card Image",
    "twitter_card_site": "Twitter Card Account",
    "twitter_card_type": "Twitter Card Type",
}

#: Human-readable status labels. Never emits engineering jargon.
_STATUS_LABELS = {
    "PASS": "Present",
    "PRESENT": "Present",
    "DETECTED": "Detected",
    "NOT DETECTED": "Not detected",
    "NOT_DETECTED": "Not detected",
    "NOT SET": "Not detected",
    "NOT FOUND": "Not detected",
    "NONE": "None detected",
    "LIMITED": "Limited scan",
    "COMPLETE": "Complete scan",
    "PARTIAL": "Partial scan",
    "HIGH": "High",
    "MEDIUM": "Medium",
    "LOW": "Low",
    "YES": "Yes",
    "NO": "No",
    "TRUE": "Yes",
    "FALSE": "No",
    "AVAILABLE": "Available",
    "ABSENT": "Not detected",
    "INDEXABLE": "Open to indexing",
    "NOINDEX": "Blocked from indexing",
}


def hr() -> str:
    """Return a horizontal rule."""
    return "---"


def section(title: str, content: str = "", level: int = 2) -> str:
    """Render a titled section at the requested heading level."""
    marker = "#" * level
    parts = [f"{marker} {title}"]
    if content:
        parts.append(content)
    return "\n\n".join(parts)


def subsection(title: str, content: str = "") -> str:
    """Render a level-3 section."""
    return section(title, content, level=3)


def escape_cell(value: object) -> str:
    """Render a value so it is safe inside a Markdown table cell."""
    text = clean_text(str(value))
    return text.replace("|", "\\|")


def table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    """Render a Markdown table, escaping every cell.

    Returns an empty string when there is nothing to render, so callers can
    fall back to an explanatory sentence instead of an empty table.
    """
    materialized = [list(row) for row in rows]
    if not headers or not materialized:
        return ""
    lines = ["| " + " | ".join(escape_cell(h) for h in headers) + " |"]
    lines.append("| " + " | ".join("-" * max(len(str(h)), 3) for h in headers) + " |")
    for row in materialized:
        lines.append("| " + " | ".join(escape_cell(cell) for cell in row) + " |")
    return "\n".join(lines)


def bullet_list(items: Sequence[str], indent: int = 0) -> str:
    """Render a bullet list."""
    if not items:
        return ""
    prefix = "  " * indent + "- "
    return "\n".join(f"{prefix}{item}" for item in items)


def numbered_list(items: Sequence[str]) -> str:
    """Render an ordered list."""
    if not items:
        return ""
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def key_value_pairs(
    pairs: Sequence[tuple[str, str]],
    headers: tuple[str, str] = ("Item", "Value"),
) -> str:
    """Render key/value pairs as a two-column table."""
    if not pairs:
        return ""
    return table(list(headers), [[key, value] for key, value in pairs])


def status_badge(status: str) -> str:
    """Map an internal status token to a business-readable label."""
    return _STATUS_LABELS.get(status.strip().upper(), status)


def rating(percentage: int) -> str:
    """Describe a coverage percentage in plain language."""
    if percentage >= 90:
        return "Strong"
    if percentage >= 70:
        return "Good"
    if percentage >= 40:
        return "Partial"
    if percentage > 0:
        return "Minimal"
    return "None detected"


def score_bar(score: int, max_score: int = 100) -> str:
    """Render a fixed-width textual score bar."""
    filled = min(score, max_score)
    pct = filled / max_score if max_score else 0.0
    bar_length = 20
    filled_length = round(bar_length * pct)
    bar = "#" * filled_length + "-" * (bar_length - filled_length)
    return f"`{bar}` {score}/{max_score}"


def clean_text(text: str) -> str:
    """Collapse all whitespace runs into single spaces and trim."""
    return " ".join(str(text).split())


def truncate_text(text: str, limit: int) -> str:
    """Truncate on a word boundary, appending a single ellipsis character."""
    cleaned = clean_text(text)
    if limit <= 0 or len(cleaned) <= limit:
        return cleaned
    window = cleaned[:limit]
    if " " in window:
        window = window[: window.rindex(" ")]
    trimmed = window.rstrip(" ,.;:-\u2013\u2014")
    if not trimmed:
        trimmed = cleaned[:limit]
    return f"{trimmed}{_ELLIPSIS}"


def humanize_label(key: str) -> str:
    """Convert a machine key such as ``CONTENT_HEADING`` into a label."""
    normalized = clean_text(key).replace("-", "_").replace(" ", "_").strip("_")
    if not normalized:
        return ""
    override = _LABEL_OVERRIDES.get(normalized.lower())
    if override is not None:
        return override
    words: list[str] = []
    for raw_word in normalized.split("_"):
        if not raw_word:
            continue
        acronym = _ACRONYMS.get(raw_word.lower())
        if acronym is not None:
            words.append(acronym)
        elif raw_word.isupper():
            words.append(raw_word.capitalize())
        elif raw_word[:1].isupper():
            words.append(raw_word)
        else:
            words.append(raw_word.capitalize())
    return " ".join(words)


def humanize_value(value: object, empty: str = "Not available") -> str:
    """Render any evidence value as readable text.

    Dictionaries become ``Label: value`` pairs, lists become comma-separated
    text, and booleans become ``Yes``/``No``. Raw Python object notation is
    never emitted.
    """
    if value is None:
        return empty
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, str):
        return clean_text(value) or empty
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, Mapping):
        parts: list[str] = []
        for key, item in value.items():
            rendered = humanize_value(item, empty="")
            if not rendered:
                continue
            label = humanize_label(str(key))
            parts.append(f"{label}: {rendered}" if label else rendered)
        return "; ".join(parts) if parts else empty
    if isinstance(value, Sequence | set | frozenset):
        rendered_items = [humanize_value(item, empty="") for item in value]
        kept = [item for item in rendered_items if item]
        return ", ".join(kept) if kept else empty
    return clean_text(str(value)) or empty


def join_sections(sections: Sequence[str]) -> str:
    """Join non-empty sections with a blank line between them."""
    return "\n\n".join(s for s in sections if s)
