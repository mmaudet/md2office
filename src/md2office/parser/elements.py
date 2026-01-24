"""AST element classes for intermediate representation."""

from __future__ import annotations

from typing import Literal

import msgspec


class TextSpan(msgspec.Struct, frozen=True):
    """A span of text with inline formatting.

    TextSpan represents the smallest unit of formatted text in the AST. Multiple
    formatting flags can be combined on a single span, and spans are typically
    grouped into lists to form paragraph or heading content.

    Attributes:
        text: The raw text content of this span. May contain newlines for soft/hard
            breaks. Never None, but can be empty string for zero-width spans.
        bold: Apply bold formatting (Markdown: **text** or __text__). Can combine
            with italic, strikethrough, code, and link.
        italic: Apply italic formatting (Markdown: *text* or _text_). Can combine
            with bold, strikethrough, code, and link.
        code: Apply inline code formatting (Markdown: `text`). Renders with monospace
            font. Can combine with other flags, though typically appears alone except
            when inside a link.
        strikethrough: Apply strikethrough formatting (Markdown: ~~text~~). Can
            combine with bold, italic, code, and link.
        link: Optional hyperlink URL. When set, the text becomes clickable. Link
            formatting can combine with all other formatting flags (bold, italic,
            code, strikethrough), allowing rich formatting of link text.

    Formatting Combination Rules:
        - All five formatting flags (bold, italic, code, strikethrough) can be
          combined in any combination on a single TextSpan.
        - The `link` field is orthogonal to text formatting - it specifies the
          hyperlink target and can be applied regardless of other formatting.
        - When multiple formatting flags are True, the renderer applies all of them
          cumulatively (e.g., bold + italic = bold italic text).
        - The most common combinations are:
            * bold + italic (***text***)
            * bold/italic with link (**[text](url)**)
            * code with link (`[code](url)`)

    Link and Code Interaction:
        - code=True with link="url" creates a clickable monospace span
        - The code flag affects visual rendering (font family, background)
        - The link flag affects behavior (hyperlink target)
        - These are independent: you can have code without link, link without code,
          or both together
        - Example Markdown: [`code link`](https://example.com) produces
          TextSpan(text="code link", code=True, link="https://example.com")

    Edge Cases:
        - Empty text (text=""): Valid, used for zero-width formatting boundaries
        - Newlines in text: Used for line breaks (linebreak and softbreak tokens)
        - link="" (empty string): Treated as no link (renderer may handle as None)
        - All flags False, link=None: Plain unformatted text
        - All flags True with link: Fully formatted hyperlink (rare but valid)

    Examples:
        Plain text:
            TextSpan(text="hello")

        Bold text:
            TextSpan(text="hello", bold=True)

        Bold italic text (Markdown: ***hello***):
            TextSpan(text="hello", bold=True, italic=True)

        Inline code (Markdown: `code`):
            TextSpan(text="code", code=True)

        Bold link (Markdown: **[text](url)**):
            TextSpan(text="text", bold=True, link="https://example.com")

        Code link (Markdown: [`code`](url)):
            TextSpan(text="code", code=True, link="https://example.com")

        Complex combination (bold + italic + strikethrough + link):
            TextSpan(
                text="fancy",
                bold=True,
                italic=True,
                strikethrough=True,
                link="https://example.com"
            )

    Usage:
        TextSpans are created by DocxRenderer during Markdown parsing and consumed
        by DocxBuilder when generating Word documents. They are immutable (frozen=True)
        and should not be modified after creation. To change formatting, create a new
        TextSpan with the desired attributes.
    """

    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    strikethrough: bool = False
    link: str | None = None


class DocxElement(msgspec.Struct, frozen=True, tag=True):
    """Base class for all block-level elements in the DOCX AST.

    DocxElement is the root of the element hierarchy representing block-level
    Markdown constructs (paragraphs, headings, lists, tables, etc.). It uses
    msgspec's tagged union feature to enable efficient serialization and type-safe
    polymorphism across all element types.

    Tagged Union Architecture:
        The `tag=True` parameter enables msgspec tagged unions, which provide:
        - Type discrimination: Each subclass gets a unique tag field for runtime
          type identification (e.g., "heading", "paragraph", "table")
        - Efficient serialization: msgspec can serialize/deserialize the correct
          subclass based on the tag without custom logic
        - Type safety: Static type checkers can verify element types in lists
        - Pattern matching: Enables exhaustive type matching in Python 3.10+

        Subclasses specify their tag with `tag="name"`:
            class DocxHeading(DocxElement, frozen=True, tag="heading"):
                ...

        When serialized, elements include their tag:
            {"type": "heading", "level": 1, "content": [...]}

    Immutability:
        All elements are frozen (`frozen=True`), making them immutable after creation.
        This ensures:
        - Thread safety: Elements can be safely shared across threads
        - Hashability: Elements can be used as dict keys or in sets
        - Predictability: Once created, elements cannot be accidentally modified
        - Performance: msgspec optimizes frozen structs with __slots__

    Subclass Hierarchy:
        Block-level elements (inherit from DocxElement):
        - DocxHeading: H1-H6 headings with optional anchors
        - DocxParagraph: Text paragraphs with inline formatting
        - DocxCodeBlock: Fenced/indented code blocks with syntax highlighting
        - DocxBlockquote: Blockquotes containing nested elements
        - DocxList: Ordered/unordered lists with nested items
        - DocxTable: Tables with rows, cells, and formatting
        - DocxImage: Image references with alt text and titles
        - DocxHorizontalRule: Thematic breaks (---, ***, ___)
        - DocxAdmonition: Callout blocks (NOTE, WARNING, etc.)

        Helper structs (do NOT inherit from DocxElement):
        - TextSpan: Inline formatted text (not a block element)
        - DocxListItem: Individual list items (wrapped by DocxList)
        - DocxTableRow: Table rows (wrapped by DocxTable)
        - DocxTableCell: Table cells (wrapped by DocxTableRow)

    Usage in the Pipeline:
        1. DocxRenderer (parser/renderer.py) creates DocxElement instances from
           Markdown tokens during parsing
        2. Elements form an AST (Abstract Syntax Tree) representing document structure
        3. DocxBuilder (builder/docx_builder.py) consumes elements to generate
           Word documents using python-docx
        4. Elements can be serialized to JSON for caching or API responses

    Examples:
        Type discrimination in a list:
            elements: list[DocxElement] = [
                DocxHeading(level=1, content=[...]),
                DocxParagraph(content=[...]),
                DocxTable(rows=[...]),
            ]
            # msgspec knows each element's type from its tag

        Pattern matching (Python 3.10+):
            match element:
                case DocxHeading(level=1):
                    # Handle H1
                case DocxParagraph(content=spans):
                    # Handle paragraph
                case DocxTable(rows=rows):
                    # Handle table

        Serialization with msgspec:
            import msgspec
            elements = [DocxHeading(level=1, content=[...])]
            json_bytes = msgspec.json.encode(elements)
            decoded = msgspec.json.decode(json_bytes, type=list[DocxElement])
            # msgspec automatically deserializes to correct subclass

    Design Rationale:
        - msgspec over dataclasses: 10-100x faster serialization/deserialization
        - Tagged unions over manual type fields: Type-safe polymorphism
        - Frozen structs: Immutability prevents bugs and enables optimizations
        - No base fields: DocxElement is purely structural, subclasses define all data

    See Also:
        - TextSpan: Inline formatting elements (not block-level)
        - DocxRenderer: Creates DocxElement instances from Markdown
        - DocxBuilder: Consumes DocxElement instances to build Word documents
        - msgspec documentation: https://jcristharif.com/msgspec/structs.html#tagged-unions
    """

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
