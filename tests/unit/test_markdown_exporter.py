"""Unit tests for the Markdown Exporter module."""

from __future__ import annotations

from pathlib import Path

import pytest

from aifme_scout.exporters.markdown_exporter import export, export_to_file
from aifme_scout.utils.models import Summary


class TestEmptySummary:
    """Tests for exporting an empty ScoutSummary."""

    def test_empty_summary_returns_empty_string(self) -> None:
        summary = Summary(text="", evidence_refs=[])
        result = export(summary)
        assert result == ""

    def test_empty_summary_never_mutates_input(self) -> None:
        summary = Summary(text="", evidence_refs=[])
        original_text = summary.text
        original_refs = list(summary.evidence_refs)
        export(summary)
        assert summary.text == original_text
        assert summary.evidence_refs == original_refs


class TestCompleteSummary:
    """Tests for exporting a complete ScoutSummary."""

    def test_complete_summary_preserves_text(self) -> None:
        text = (
            "## Executive Summary\nTarget site: https://example.com\n\n"
            "## Diagnostics\nseo_items: 1\n"
        )
        summary = Summary(text=text, evidence_refs=["ev-000001", "https://example.com"])
        result = export(summary)
        assert result == text

    def test_complete_summary_preserves_evidence_refs_in_text(self) -> None:
        text = "Evidence ref: ev-000001\n"
        summary = Summary(text=text, evidence_refs=["ev-000001"])
        result = export(summary)
        assert "ev-000001" in result

    def test_complete_summary_all_sections_preserved(self) -> None:
        text = "\n\n".join(
            [
                "## Executive Summary\nTarget site: https://example.com",
                "## Website Overview\nURL: https://example.com",
                "## SEO Summary\nTitle: Test",
                "## Metadata Summary\nGenerator: WordPress",
                "## Technology Summary\nReact",
                "## Content Summary\nHello world",
                "## Social Presence Summary\nTwitter: @test",
                "## Competitor Summary\nCompetitor A",
                "## Diagnostics\ntotal_evidence_items: 5",
                "## Data Completeness\nSEO: 1 items (complete)",
            ]
        )
        summary = Summary(text=text, evidence_refs=["ev-000001"])
        result = export(summary)
        assert "## Executive Summary" in result
        assert "## Website Overview" in result
        assert "## SEO Summary" in result
        assert "## Metadata Summary" in result
        assert "## Technology Summary" in result
        assert "## Content Summary" in result
        assert "## Social Presence Summary" in result
        assert "## Competitor Summary" in result
        assert "## Diagnostics" in result
        assert "## Data Completeness" in result


class TestStableRendering:
    """Tests for stable, deterministic rendering."""

    def test_same_input_same_output(self) -> None:
        text = "## Executive Summary\nTarget site: https://example.com\n"
        summary = Summary(text=text, evidence_refs=["ev-000001"])
        result1 = export(summary)
        result2 = export(summary)
        assert result1 == result2

    def test_deterministic_rendering(self) -> None:
        text = "## Diagnostics\nseo_items: 1\nmetadata_items: 0\n"
        summary = Summary(text=text, evidence_refs=["ev-000001"])
        results = [export(summary) for _ in range(5)]
        assert all(r == results[0] for r in results)


class TestUTF8Encoding:
    """Tests for UTF-8 encoding support."""

    def test_utf8_characters_preserved(self) -> None:
        text = "## Executive Summary\nCafé résumé naïve 日本語\n"
        summary = Summary(text=text, evidence_refs=[])
        result = export(summary)
        assert "Café résumé naïve 日本語" in result
        result.encode("utf-8").decode("utf-8")

    def test_export_to_file_writes_utf8(self, tmp_path: Path) -> None:
        text = "## Executive Summary\nCafé résumé naïve 日本語\n"
        summary = Summary(text=text, evidence_refs=[])
        file_path = tmp_path / "report.md"
        export_to_file(summary, file_path)
        content = file_path.read_text(encoding="utf-8")
        assert "Café résumé naïve 日本語" in content


class TestFileExport:
    """Tests for export_to_file."""

    def test_file_export_writes_content(self, tmp_path: Path) -> None:
        text = "## Executive Summary\nTarget site: https://example.com\n"
        summary = Summary(text=text, evidence_refs=[])
        file_path = tmp_path / "report.md"
        export_to_file(summary, file_path)
        assert file_path.exists()
        content = file_path.read_text(encoding="utf-8")
        assert content == f"{text}\n"

    def test_file_export_ends_with_newline(self, tmp_path: Path) -> None:
        text = "## Executive Summary\nTarget site: https://example.com"
        summary = Summary(text=text, evidence_refs=[])
        file_path = tmp_path / "report.md"
        export_to_file(summary, file_path)
        content = file_path.read_text(encoding="utf-8")
        assert content.endswith("\n")

    def test_file_export_invalid_path_raises(self) -> None:
        summary = Summary(text="", evidence_refs=[])
        with pytest.raises(OSError):
            export_to_file(summary, "/invalid/path/that/does/not/exist/report.md")


class TestRoundTripRendering:
    """Tests for round-trip text comparison."""

    def test_round_trip_preserves_text(self) -> None:
        text = (
            "## Executive Summary\nTarget site: https://example.com\n\n"
            "## Diagnostics\nseo_items: 1\n"
        )
        summary = Summary(text=text, evidence_refs=["ev-000001"])
        result = export(summary)
        assert result == text

    def test_round_trip_preserves_evidence_refs(self) -> None:
        text = "Evidence: ev-000001, ev-000002\n"
        refs = ["ev-000001", "ev-000002", "https://example.com"]
        summary = Summary(text=text, evidence_refs=refs)
        result = export(summary)
        assert result == text
        assert summary.evidence_refs == refs

    def test_round_trip_empty_summary(self) -> None:
        summary = Summary(text="", evidence_refs=[])
        result = export(summary)
        assert result == ""


class TestDeterministicRendering:
    """Tests for deterministic rendering."""

    def test_deterministic_output_across_calls(self) -> None:
        text = "## Executive Summary\nTarget site: https://example.com\n"
        summary = Summary(text=text, evidence_refs=["ev-000001"])
        outputs = [export(summary) for _ in range(10)]
        assert all(o == outputs[0] for o in outputs)

    def test_unicode_deterministic(self) -> None:
        text = "## Executive Summary\nCafé résumé naïve 日本語\n"
        summary = Summary(text=text, evidence_refs=[])
        result1 = export(summary)
        result2 = export(summary)
        assert result1 == result2

    def test_never_mutates_input(self) -> None:
        text = "## Executive Summary\nTarget site: https://example.com\n"
        refs = ["ev-000001"]
        summary = Summary(text=text, evidence_refs=refs)
        export(summary)
        assert summary.text == text
        assert summary.evidence_refs == refs
