"""Markdown Exporter for ScoutSummary.

Renders a ScoutSummary into a deterministic Markdown document.
This is a rendering layer only; it does not summarize, infer, classify,
or modify the summary content.
"""

from __future__ import annotations

from pathlib import Path

from aifme_scout.utils.models import Summary


def export(summary: Summary) -> str:
    """Serialize a ScoutSummary to a Markdown string.

    The output preserves the summary text exactly, including section
    headings, wording, and evidence references. No additional text is
    injected.

    Args:
        summary: The ScoutSummary to render.

    Returns:
        A Markdown string representing the summary.
    """
    return summary.text


def export_to_file(summary: Summary, path: str | Path) -> None:
    """Serialize a ScoutSummary and write it to a file.

    Args:
        summary: The ScoutSummary to render.
        path: File path to write the Markdown output to.

    Raises:
        OSError: If the file cannot be written.
    """
    content = export(summary)
    Path(path).write_text(f"{content}\n", encoding="utf-8")
