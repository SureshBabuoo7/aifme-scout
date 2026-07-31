"""Parser package."""

from aifme_scout.parser.models import Element, ParsedPage, ParsedSite, ParseError, ParseWarning
from aifme_scout.parser.parser import parse

__all__ = ["Element", "ParseError", "ParseWarning", "ParsedPage", "ParsedSite", "parse"]
