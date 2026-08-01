"""Extractors package."""

from aifme_scout.extractors.metadata import extract as extract_metadata
from aifme_scout.extractors.models import (
    CanonicalURL,
    ElementProvenance,
    Heading,
    HeadingHierarchy,
    Indexability,
    MetadataPageResult,
    MetadataResult,
    MetaDescription,
    MetaLink,
    MetaValue,
    OpenGraphSEO,
    RobotsMeta,
    SEOPageResult,
    SEOResult,
    StructuredDataPresence,
    Title,
    TwitterCardSEO,
    VerificationTag,
)
from aifme_scout.extractors.seo import analyze, to_simple_seo

__all__ = [
    "analyze",
    "extract_metadata",
    "to_simple_seo",
    "CanonicalURL",
    "ElementProvenance",
    "Heading",
    "HeadingHierarchy",
    "Indexability",
    "MetaDescription",
    "MetaLink",
    "MetaValue",
    "MetadataPageResult",
    "MetadataResult",
    "OpenGraphSEO",
    "RobotsMeta",
    "SEOPageResult",
    "SEOResult",
    "StructuredDataPresence",
    "Title",
    "TwitterCardSEO",
    "VerificationTag",
]
