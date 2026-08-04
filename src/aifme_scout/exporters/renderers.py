"""Reusable Markdown renderers for the Website Intelligence Report.

Each helper produces a deterministic, self-contained Markdown fragment.
No AI, no inference, no invented facts — only deterministic transformations
of collected evidence.
"""

from __future__ import annotations


def hr() -> str:
    return "---"


def section(title: str, content: str = "", level: int = 2) -> str:
    marker = "#" * level
    parts = [f"{marker} {title}"]
    if content:
        parts.append(content)
    return "\n\n".join(parts)


def subsection(title: str, content: str = "") -> str:
    return section(title, content, level=3)


def table(headers: list[str], rows: list[list[str]]) -> str:
    if not headers or not rows:
        return ""
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("-" * len(h) for h in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def bullet_list(items: list[str], indent: int = 0) -> str:
    prefix = "  " * indent + "- "
    if not items:
        return ""
    return "\n".join(f"{prefix}{item}" for item in items)


def key_value_pairs(pairs: list[tuple[str, str]]) -> str:
    if not pairs:
        return ""
    return table(["Item", "Value"], [[k, v] for k, v in pairs])


def status_badge(status: str) -> str:
    mapping = {
        "PASS": "PASS",
        "FAIL": "FAIL",
        "MISSING": "MISSING",
        "LIMITED": "WARN",
        "WARN": "WARN",
        "NOT FOUND": "NOT FOUND",
        "HIGH": "High",
        "MEDIUM": "Medium",
        "LOW": "Low",
        "YES": "Yes",
        "NO": "No",
        "TRUE": "Yes",
        "FALSE": "No",
        "AVAILABLE": "Available",
        "ABSENT": "Absent",
        "PRESENT": "Present",
        "INDEXABLE": "Indexable",
        "NOINDEX": "Noindex",
    }
    return mapping.get(status.upper(), status)


def score_bar(score: int, max_score: int = 100) -> str:
    filled = min(score, max_score)
    pct = filled / max_score
    bar_length = 20
    filled_length = round(bar_length * pct)
    bar = "#" * filled_length + "-" * (bar_length - filled_length)
    return f"`{bar}` {score}/{max_score}"


def join_sections(sections: list[str]) -> str:
    return "\n\n".join(s for s in sections if s)
