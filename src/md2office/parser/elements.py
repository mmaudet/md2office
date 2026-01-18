"""AST element classes for intermediate representation."""

from __future__ import annotations

from typing import Literal

import msgspec


class TextSpan(msgspec.Struct, frozen=True):
    """A span of text with formatting."""

    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    strikethrough: bool = False
    link: str | None = None


class DocxElement(msgspec.Struct, frozen=True, tag=True):
    """Base class for all DOCX elements."""

    pass


class DocxHeading(DocxElement, frozen=True, tag="heading"):
    """Heading element (H1-H6)."""

    level: int
    content: list[TextSpan]
    anchor: str | None = None  # Bookmark anchor for internal links


class DocxParagraph(DocxElement, frozen=True, tag="paragraph"):
    """Paragraph element with inline formatting."""

    content: list[TextSpan]


class DocxCodeBlock(DocxElement, frozen=True, tag="code_block"):
    """Fenced code block."""

    code: str
    language: str | None = None


class DocxBlockquote(DocxElement, frozen=True, tag="blockquote"):
    """Blockquote element containing other elements."""

    children: list[DocxElement]


class DocxListItem(msgspec.Struct, frozen=True):
    """A single list item."""

    content: list[TextSpan]
    children: list[DocxElement] = msgspec.field(default_factory=list)


class DocxList(DocxElement, frozen=True, tag="list"):
    """Ordered or unordered list."""

    ordered: bool
    items: list[DocxListItem]
    start: int = 1


class DocxTableCell(msgspec.Struct, frozen=True):
    """Table cell."""

    content: list[TextSpan]
    is_header: bool = False
    colspan: int = 1
    rowspan: int = 1
    merge_up: bool = False  # Indicates cell should merge with cell above (^^)
    merge_left: bool = False  # Indicates cell should merge with cell to the left (>>)


class DocxTableRow(msgspec.Struct, frozen=True):
    """Table row."""

    cells: list[DocxTableCell]


class DocxTable(DocxElement, frozen=True, tag="table"):
    """Table element."""

    rows: list[DocxTableRow]
    has_header: bool = True


class DocxImage(DocxElement, frozen=True, tag="image"):
    """Image element."""

    src: str
    alt: str = ""
    title: str | None = None


class DocxHorizontalRule(DocxElement, frozen=True, tag="hr"):
    """Horizontal rule / thematic break."""

    pass


AdmonitionType = Literal["NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"]


class DocxAdmonition(DocxElement, frozen=True, tag="admonition"):
    """Admonition/callout block (NOTE, WARNING, etc.)."""

    admonition_type: AdmonitionType
    title: str | None = None
    children: list[DocxElement] = msgspec.field(default_factory=list)


# Type alias for document content
Document = list[DocxElement]
