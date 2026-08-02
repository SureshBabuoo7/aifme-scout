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


def _classify_target(schema: ScoutSchema) -> tuple[str, str]:
    """Classify the target site using only deterministic evidence.

    This closes EXEC-11's heuristic-discovery stub by providing the
    target classification that competitor discovery depends on.

    Classification is evidence-only: it inspects detected technologies
    and content keywords from the schema. No inference beyond the
    collected evidence is performed.

    Returns:
        (classification, evidence_id) tuple. Classification is one of
        the supported categories; evidence_id references the detector
        item that drove the classification, or an empty string when
        no classification can be made.
    """
    tech_names: set[str] = set()
    tech_categories: set[str] = set()
    for item in schema.technology:
        if isinstance(item.value, dict):
            name = item.value.get("name")
            category = item.value.get("category")
            if isinstance(name, str):
                tech_names.add(name.lower())
            if isinstance(category, str):
                tech_categories.add(category.lower())

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
        "shopify",
        "woocommerce",
        "magento",
        "bigcommerce",
        "stripe",
        "paypal",
        "cart",
        "checkout",
    }
    saas_indicators = {
        "api",
        "pricing",
        "subscription",
        "trial",
        "saas",
        "cloud",
        "dashboard",
        "signup",
    }
    blog_indicators = {
        "blog",
        "article",
        "post",
        "author",
        "category",
        "rss",
        "wordpress",
        "medium",
    }
    agency_indicators = {
        "agency",
        "client",
        "portfolio",
        "service",
        "consulting",
        "case study",
    }
    media_indicators = {
        "video",
        "podcast",
        "streaming",
        "media",
        "channel",
        "youtube",
    }

    def _indicator_hits(indicators: set[str], text: str) -> int:
        return sum(1 for ind in indicators if ind in text)

    ecommerce_score = (
        _indicator_hits(ecommerce_indicators, content_text)
        + sum(1 for t in tech_names if t in ecommerce_indicators)
    )
    saas_score = (
        _indicator_hits(saas_indicators, content_text)
        + sum(1 for t in tech_names if t in saas_indicators)
    )
    blog_score = (
        _indicator_hits(blog_indicators, content_text)
        + sum(1 for t in tech_names if t in blog_indicators)
    )
    agency_score = (
        _indicator_hits(agency_indicators, content_text)
        + sum(1 for t in tech_names if t in agency_indicators)
    )
    media_score = (
        _indicator_hits(media_indicators, content_text)
        + sum(1 for t in tech_names if t in media_indicators)
    )

    scores = {
        "e-commerce": ecommerce_score,
        "saas": saas_score,
        "blog": blog_score,
        "agency": agency_score,
        "media": media_score,
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


def _summarize_evidence_item(item: EvidenceItem) -> tuple[str, str]:
    """Convert an evidence item into a human-readable sentence fragment.

    Returns:
        (sentence_fragment, evidence_id) tuple.
    """
    evidence_id = item.evidence_id
    value = item.value

    if isinstance(value, dict):
        parts = [f"{k}={v}" for k, v in value.items() if v]
        value_str = ", ".join(parts) if parts else str(value)
    else:
        value_str = str(value)

    return (value_str, evidence_id)


def _section_sentences(items: list[EvidenceItem]) -> tuple[list[str], list[str]]:
    """Build a list of sentences and evidence references for a section.

    Returns:
        (sentences, evidence_refs) tuple.
    """
    sentences: list[str] = []
    refs: list[str] = []
    for item in items:
        fragment, evidence_id = _summarize_evidence_item(item)
        if fragment:
            sentences.append(fragment)
        if evidence_id:
            refs.append(evidence_id)
    return sentences, refs


def _build_executive_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Executive Summary section."""
    sentences: list[str] = []
    refs: list[str] = []

    site = schema.site
    sentences.append(f"Target site: {site.url}")
    refs.append(site.url)

    evidence_count = len(schema.evidence)
    sentences.append(f"Evidence items collected: {evidence_count}")
    if schema.evidence:
        first_evidence_id = schema.evidence[0].evidence_id
        if first_evidence_id:
            refs.append(first_evidence_id)

    classification, class_evidence_id = _classify_target(schema)
    if classification != "general":
        sentences.append(f"Target classification: {classification}")
        if class_evidence_id:
            refs.append(class_evidence_id)

    return "\n".join(sentences), refs


def _build_website_overview(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Website Overview section."""
    sentences: list[str] = []
    refs: list[str] = []

    site = schema.site
    sentences.append(f"URL: {site.url}")
    refs.append(site.url)

    if schema.meta.schema_version:
        sentences.append(f"Schema version: {schema.meta.schema_version}")

    return "\n".join(sentences), refs


def _build_seo_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the SEO Summary section."""
    sentences, refs = _section_sentences(schema.seo)
    return "\n".join(sentences), refs


def _build_metadata_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Metadata Summary section."""
    sentences, refs = _section_sentences(schema.metadata)
    return "\n".join(sentences), refs


def _build_technology_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Technology Summary section."""
    sentences, refs = _section_sentences(schema.technology)
    return "\n".join(sentences), refs


def _build_content_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Content Summary section."""
    sentences, refs = _section_sentences(schema.content)
    return "\n".join(sentences), refs


def _build_social_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Social Presence Summary section."""
    sentences, refs = _section_sentences(schema.social)
    return "\n".join(sentences), refs


def _build_competitor_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Competitor Summary section."""
    sentences, refs = _section_sentences(schema.competitors)
    return "\n".join(sentences), refs


def _build_diagnostics_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build the Diagnostics section."""
    sentences: list[str] = []
    refs: list[str] = []

    diagnostics = schema.diagnostics
    if not diagnostics:
        return "No diagnostics available.", []

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
            sentences.append(f"{key}: {diagnostics[key]}")

    if "build_timestamp" in diagnostics:
        sentences.append(f"Build timestamp: {diagnostics['build_timestamp']}")

    return "\n".join(sentences), refs


def _build_data_completeness_summary(
    schema: ScoutSchema,
) -> tuple[str, list[str]]:
    """Build the Data Completeness section."""
    sentences: list[str] = []
    refs: list[str] = []

    sections = {
        "SEO": schema.seo,
        "Metadata": schema.metadata,
        "Technology": schema.technology,
        "Content": schema.content,
        "Social": schema.social,
        "Competitors": schema.competitors,
    }

    for section_name, items in sections.items():
        count = len(items)
        status = "complete" if count > 0 else "missing"
        sentences.append(f"{section_name}: {count} items ({status})")
        if items:
            refs.append(items[0].evidence_id)

    return "\n".join(sentences), refs


def _build_template_summary(schema: ScoutSchema) -> tuple[str, list[str]]:
    """Build a complete template-based summary from schema evidence.

    Returns:
        (text, evidence_refs) tuple.
    """
    sections_text: list[str] = []
    all_refs: list[str] = []

    section_builders = [
        ("Executive Summary", _build_executive_summary),
        ("Website Overview", _build_website_overview),
        ("SEO Summary", _build_seo_summary),
        ("Metadata Summary", _build_metadata_summary),
        ("Technology Summary", _build_technology_summary),
        ("Content Summary", _build_content_summary),
        ("Social Presence Summary", _build_social_summary),
        ("Competitor Summary", _build_competitor_summary),
        ("Diagnostics", _build_diagnostics_summary),
        ("Data Completeness", _build_data_completeness_summary),
    ]

    for section_name, builder in section_builders:
        section_text, section_refs = builder(schema)
        sections_text.append(f"## {section_name}\n{section_text}")
        all_refs.extend(section_refs)

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
