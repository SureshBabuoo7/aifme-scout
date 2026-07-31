"""Extractors package."""

from aifme_scout.extractors.models import (
    CanonicalURL,
    Heading,
    HeadingHierarchy,
    Indexability,
    MetaDescription,
    OpenGraphSEO,
    RobotsMeta,
    SEOPageResult,
    SEOResult,
    StructuredDataPresence,
    Title,
    TwitterCardSEO,
)
from aifme_scout.extractors.seo import analyze, to_simple_seo

__all__ = [
    "analyze",
    "to_simple_seo",
    "CanonicalURL",
    "Heading",
    "HeadingHierarchy",
    "Indexability",
    "MetaDescription",
    "OpenGraphSEO",
    "RobotsMeta",
    "SEOPageResult",
    "SEOResult",
    "StructuredDataPresence",
    "Title",
    "TwitterCardSEO",
]
