"""Custom mistune renderer that produces DOCX AST elements."""

from __future__ import annotations

import re
from typing import Any

import mistune

from md2office.parser.elements import (
    DocxAdmonition,
    DocxBlockquote,
    DocxCodeBlock,
    DocxElement,
    DocxHeading,
    DocxHorizontalRule,
    DocxImage,
    DocxList,
    DocxListItem,
    DocxParagraph,
    DocxTable,
    DocxTableCell,
    DocxTableRow,
    TextSpan,
)

# Pattern for GitHub-style admonitions: > [!NOTE], > [!WARNING], etc.
ADMONITION_PATTERN = re.compile(
    r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$", re.IGNORECASE
)


class DocxRenderer(mistune.BaseRenderer):
    """Custom renderer that produces DOCX AST elements instead of HTML."""

    NAME = "docx"

    def __init__(self) -> None:
        super().__init__()

    def _render_children(self, token: dict, state: Any) -> list:
        """Render children tokens."""
        children = token.get("children", [])
        result = []
        for child in children:
            func = self._get_method(child["type"])
            rendered = func(child, state)
            if rendered is not None:
                result.append(rendered)
        return result

    # -------------------------------------------------------------------------
    # Inline elements - receive token dict
    # -------------------------------------------------------------------------

    def text(self, token: dict, state: Any) -> TextSpan:
        """Plain text."""
        return TextSpan(text=token.get("raw", ""))

    def emphasis(self, token: dict, state: Any) -> list[TextSpan]:
        """Italic text (*text* or _text_)."""
        children = self._render_children(token, state)
        spans = self._flatten_inline(children)
        return [
            TextSpan(
                text=span.text,
                bold=span.bold,
                italic=True,
                code=span.code,
                strikethrough=span.strikethrough,
                link=span.link,
            )
            for span in spans
        ]

    def strong(self, token: dict, state: Any) -> list[TextSpan]:
        """Bold text (**text** or __text__)."""
        children = self._render_children(token, state)
        spans = self._flatten_inline(children)
        return [
            TextSpan(
                text=span.text,
                bold=True,
                italic=span.italic,
                code=span.code,
                strikethrough=span.strikethrough,
                link=span.link,
            )
            for span in spans
        ]

    def codespan(self, token: dict, state: Any) -> TextSpan:
        """Inline code (`code`)."""
        return TextSpan(text=token.get("raw", ""), code=True)

    def strikethrough(self, token: dict, state: Any) -> list[TextSpan]:
        """Strikethrough text (~~text~~)."""
        children = self._render_children(token, state)
        spans = self._flatten_inline(children)
        return [
            TextSpan(
                text=span.text,
                bold=span.bold,
                italic=span.italic,
                code=span.code,
                strikethrough=True,
                link=span.link,
            )
            for span in spans
        ]

    def link(self, token: dict, state: Any) -> list[TextSpan]:
        """Hyperlink [text](url)."""
        children = self._render_children(token, state)
        spans = self._flatten_inline(children)
        attrs = token.get("attrs", {})
        url = attrs.get("url", "") or token.get("link", "")
        return [
            TextSpan(
                text=span.text,
                bold=span.bold,
                italic=span.italic,
                code=span.code,
                strikethrough=span.strikethrough,
                link=url,
            )
            for span in spans
        ]

    def image(self, token: dict, state: Any) -> DocxImage:
        """Image ![alt](url)."""
        attrs = token.get("attrs", {})
        return DocxImage(
            src=attrs.get("url", ""),
            alt=token.get("alt", attrs.get("alt", "")),
            title=attrs.get("title"),
        )

    def linebreak(self, token: dict, state: Any) -> TextSpan:
        """Hard line break."""
        return TextSpan(text="\n")

    def softbreak(self, token: dict, state: Any) -> TextSpan:
        """Soft line break."""
        return TextSpan(text=" ")

    # -------------------------------------------------------------------------
    # Block elements - receive token dict and state
    # -------------------------------------------------------------------------

    def paragraph(self, token: dict, state: Any) -> DocxParagraph:
        """Paragraph block."""
        children = self._render_children(token, state)
        spans = self._flatten_inline(children)
        return DocxParagraph(content=spans)

    def heading(self, token: dict, state: Any) -> DocxHeading:
        """Heading block (H1-H6)."""
        children = self._render_children(token, state)
        spans = self._flatten_inline(children)
        attrs = token.get("attrs", {})
        level = attrs.get("level", 1)

        # Generate anchor slug from heading text (like GitHub/Markdown does)
        text = "".join(span.text for span in spans)
        anchor = self._generate_anchor(text)

        return DocxHeading(level=level, content=spans, anchor=anchor)

    def blank_line(self, token: dict, state: Any) -> None:
        """Blank line - ignored."""
        return None

    def thematic_break(self, token: dict, state: Any) -> DocxHorizontalRule:
        """Horizontal rule (---, ***, ___)."""
        return DocxHorizontalRule()

    def block_code(self, token: dict, state: Any) -> DocxCodeBlock:
        """Fenced or indented code block."""
        code = token.get("raw", "")
        attrs = token.get("attrs", {})
        info = attrs.get("info", "") or token.get("info", "")
        language = info.split()[0] if info else None
        return DocxCodeBlock(code=code.rstrip("\n"), language=language)

    def block_quote(self, token: dict, state: Any) -> DocxElement:
        """Blockquote or admonition."""
        children = self._render_children(token, state)
        elements = self._flatten_blocks(children)

        # Check if this is an admonition (GitHub-style)
        if elements and isinstance(elements[0], DocxParagraph):
            first_para = elements[0]
            if first_para.content:
                first_text = first_para.content[0].text
                match = ADMONITION_PATTERN.match(first_text)
                if match:
                    admonition_type = match.group(1).upper()
                    title_text = match.group(2).strip() or None

                    # Update the first paragraph to remove the admonition marker
                    remaining_text = first_text[match.end() :].strip()
                    if remaining_text:
                        new_first_span = TextSpan(text=remaining_text)
                        new_content = [new_first_span] + list(first_para.content[1:])
                        elements[0] = DocxParagraph(content=new_content)
                    elif len(first_para.content) > 1:
                        elements[0] = DocxParagraph(content=list(first_para.content[1:]))
                    else:
                        elements = elements[1:]

                    return DocxAdmonition(
                        admonition_type=admonition_type,  # type: ignore[arg-type]
                        title=title_text,
                        children=elements,
                    )

        return DocxBlockquote(children=elements)

    def list(self, token: dict, state: Any) -> DocxList:
        """Ordered or unordered list."""
        children = self._render_children(token, state)
        items = []
        for child in children:
            if isinstance(child, DocxListItem):
                items.append(child)
        attrs = token.get("attrs", {})
        ordered = attrs.get("ordered", False)
        start = attrs.get("start", 1)
        return DocxList(ordered=ordered, items=items, start=start or 1)

    def list_item(self, token: dict, state: Any) -> DocxListItem:
        """List item."""
        children = self._render_children(token, state)
        # First paragraph becomes inline content, rest are nested elements
        content: list[TextSpan] = []
        nested: list[DocxElement] = []

        blocks = self._flatten_blocks(children)
        for i, block in enumerate(blocks):
            if i == 0 and isinstance(block, DocxParagraph):
                content = list(block.content)
            else:
                nested.append(block)

        return DocxListItem(content=content, children=nested)

    # -------------------------------------------------------------------------
    # Table elements
    # -------------------------------------------------------------------------

    def table(self, token: dict, state: Any) -> DocxTable:
        """Table block."""
        children = self._render_children(token, state)
        rows: list[DocxTableRow] = []
        has_header = False

        for child in children:
            if isinstance(child, list):
                for row in child:
                    if isinstance(row, DocxTableRow):
                        if row.cells and row.cells[0].is_header:
                            has_header = True
                        rows.append(row)
            elif isinstance(child, DocxTableRow):
                if child.cells and child.cells[0].is_header:
                    has_header = True
                rows.append(child)

        return DocxTable(rows=rows, has_header=has_header)

    def table_head(self, token: dict, state: Any) -> list[DocxTableRow]:
        """Table header section."""
        children = self._render_children(token, state)
        return self._process_table_rows(children, is_header=True)

    def table_body(self, token: dict, state: Any) -> list[DocxTableRow]:
        """Table body section."""
        children = self._render_children(token, state)
        return self._process_table_rows(children, is_header=False)

    def table_row(self, token: dict, state: Any) -> DocxTableRow:
        """Table row."""
        children = self._render_children(token, state)
        cells = [c for c in children if isinstance(c, DocxTableCell)]
        return DocxTableRow(cells=cells)

    def table_cell(self, token: dict, state: Any) -> DocxTableCell:
        """Table cell."""
        children = self._render_children(token, state)
        spans = self._flatten_inline(children)
        attrs = token.get("attrs", {})
        is_head = attrs.get("is_head", False)
        return DocxTableCell(content=spans, is_header=is_head)

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    def _flatten_inline(self, items: list[Any]) -> list[TextSpan]:
        """Flatten nested inline elements into a list of TextSpans."""
        result: list[TextSpan] = []
        for item in items:
            if isinstance(item, TextSpan):
                result.append(item)
            elif isinstance(item, list):
                result.extend(self._flatten_inline(item))
            elif isinstance(item, DocxImage):
                # Images in inline context: add placeholder text
                result.append(TextSpan(text=f"[Image: {item.alt or item.src}]"))
            elif item is None:
                pass
            else:
                # Convert other types to string
                result.append(TextSpan(text=str(item)))
        return result

    def _flatten_blocks(self, items: list[Any]) -> list[DocxElement]:
        """Flatten nested block elements into a list."""
        result: list[DocxElement] = []
        for item in items:
            if isinstance(item, DocxElement):
                result.append(item)
            elif isinstance(item, list):
                result.extend(self._flatten_blocks(item))
            elif item is None:
                pass
        return result

    def _process_table_rows(
        self, children: list[Any], is_header: bool
    ) -> list[DocxTableRow]:
        """Process table rows from children."""
        rows: list[DocxTableRow] = []
        for child in children:
            if isinstance(child, DocxTableRow):
                # Update cells with header flag
                if is_header:
                    cells = [
                        DocxTableCell(content=c.content, is_header=True)
                        for c in child.cells
                    ]
                    rows.append(DocxTableRow(cells=cells))
                else:
                    rows.append(child)
        return rows

    def _generate_anchor(self, text: str) -> str:
        """Generate a URL-safe anchor slug from heading text.

        Follows GitHub-style anchor generation:
        - Convert to lowercase
        - Replace spaces with hyphens
        - Remove special characters except hyphens and underscores
        - Remove accents from characters

        Args:
            text: Heading text.

        Returns:
            Anchor slug suitable for bookmarks.
        """
        import unicodedata

        # Normalize unicode and remove accents
        normalized = unicodedata.normalize("NFD", text)
        ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

        # Convert to lowercase
        slug = ascii_text.lower()

        # Replace spaces and special chars with hyphens
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)

        # Remove leading/trailing hyphens
        slug = slug.strip("-")

        return slug or "heading"
