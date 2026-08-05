"""Data models for the HTML Parser module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def _attrs_match(attrs: dict[str, str], filter_attrs: dict[str, str] | None) -> bool:
    if filter_attrs is None:
        return True
    return all(attrs.get(k) == v for k, v in filter_attrs.items())


@dataclass(frozen=True)
class ParseWarning:
    """Non-fatal issue encountered during parsing."""

    message: str
    severity: str = "warning"


@dataclass(frozen=True)
class ParseError:
    """Fatal parse failure for a single page."""

    code: str
    message: str
    url: str


class Element:
    """Navigable DOM element wrapper.

    Provides a parser-agnostic interface over the underlying HTML tree.
    """

    __slots__ = ("_tag", "_attrs", "_text", "_children", "_parent")

    def __init__(
        self,
        tag: str,
        attrs: dict[str, str],
        text: str,
        children: list[Element],
        parent: Element | None = None,
    ) -> None:
        self._tag = tag
        self._attrs = dict(attrs)
        self._text = text
        self._children = list(children)
        self._parent = parent

    @property
    def tag(self) -> str:
        return self._tag

    @property
    def text(self) -> str:
        return self._text

    @property
    def attrs(self) -> dict[str, str]:
        return dict(self._attrs)

    def get(self, attr: str, default: str | None = None) -> str | None:
        return self._attrs.get(attr, default)

    @property
    def children(self) -> list[Element]:
        return list(self._children)

    @property
    def parent(self) -> Element | None:
        return self._parent

    def find(self, tag: str, attrs: dict[str, str] | None = None) -> Element | None:
        for child in self._children:
            if (tag in (None, "", "*", True) or child._tag == tag) and _attrs_match(child._attrs, attrs):
                return child
            found = child.find(tag, attrs)
            if found is not None:
                return found
        return None

    def find_all(self, tag: str, attrs: dict[str, str] | None = None) -> list[Element]:
        results: list[Element] = []
        for child in self._children:
            if (tag in (None, "", "*", True) or child._tag == tag) and _attrs_match(child._attrs, attrs):
                results.append(child)
            results.extend(child.find_all(tag, attrs))
        return results

    def __len__(self) -> int:
        return 1 + sum(len(child) for child in self._children)

    def __repr__(self) -> str:
        return f"Element(tag={self._tag!r}, text={self._text!r})"


@dataclass(frozen=True)
class ParsedPage:
    """Parsed representation of a single page."""

    url: str
    raw_html: str
    root: Element
    head: Element | None
    body: Element | None
    warnings: list[ParseWarning] = field(default_factory=list)
    parse_error: ParseError | None = None


@dataclass(frozen=True)
class ParsedSite:
    """Parsed representation of an entire site."""

    target_url: str
    pages: list[ParsedPage]
    parse_errors: list[ParseError] = field(default_factory=list)
