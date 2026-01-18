"""Custom mistune renderer that produces DOCX AST elements."""

from __future__ import annotations

import re
from typing import Any

import mistune

from md2office.parser.elements import (
    AdmonitionType,
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
ADMONITION_PATTERN = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$", re.IGNORECASE)


class DocxRenderer(mistune.BaseRenderer):
    """Custom renderer that produces DOCX AST elements instead of HTML."""

    NAME = "docx"

    def __init__(self) -> None:
        super().__init__()
        self._inline_stack: list[TextSpan] = []

    # -------------------------------------------------------------------------
    # Inline elements
    # -------------------------------------------------------------------------

    def text(self, text: str) -> TextSpan:
        """Plain text."""
        return TextSpan(text=text)

    def emphasis(self, children: list[TextSpan]) -> list[TextSpan]:
        """Italic text (*text* or _text_)."""
        return [
            TextSpan(
                text=span.text,
                bold=span.bold,
                italic=True,
                code=span.code,
                strikethrough=span.strikethrough,
                link=span.link,
            )
            for span in children
        ]

    def strong(self, children: list[TextSpan]) -> list[TextSpan]:
        """Bold text (**text** or __text__)."""
        return [
            TextSpan(
                text=span.text,
                bold=True,
                italic=span.italic,
                code=span.code,
                strikethrough=span.strikethrough,
                link=span.link,
            )
            for span in children
        ]

    def codespan(self, text: str) -> TextSpan:
        """Inline code (`code`)."""
        return TextSpan(text=text, code=True)

    def strikethrough(self, children: list[TextSpan]) -> list[TextSpan]:
        """Strikethrough text (~~text~~)."""
        return [
            TextSpan(
                text=span.text,
                bold=span.bold,
                italic=span.italic,
                code=span.code,
                strikethrough=True,
                link=span.link,
            )
            for span in children
        ]

    def link(self, children: list[TextSpan], url: str, title: str | None = None) -> list[TextSpan]:
        """Hyperlink [text](url)."""
        return [
            TextSpan(
                text=span.text,
                bold=span.bold,
                italic=span.italic,
                code=span.code,
                strikethrough=span.strikethrough,
                link=url,
            )
            for span in children
        ]

    def image(self, alt: str, url: str, title: str | None = None) -> DocxImage:
        """Image ![alt](url)."""
        return DocxImage(src=url, alt=alt, title=title)

    def linebreak(self) -> TextSpan:
        """Hard line break."""
        return TextSpan(text="\n")

    def softbreak(self) -> TextSpan:
        """Soft line break."""
        return TextSpan(text=" ")

    # -------------------------------------------------------------------------
    # Block elements
    # -------------------------------------------------------------------------

    def paragraph(self, children: list[Any]) -> DocxParagraph:
        """Paragraph block."""
        spans = self._flatten_inline(children)
        return DocxParagraph(content=spans)

    def heading(self, children: list[Any], level: int) -> DocxHeading:
        """Heading block (H1-H6)."""
        spans = self._flatten_inline(children)
        return DocxHeading(level=level, content=spans)

    def blank_line(self) -> None:
        """Blank line - ignored."""
        return None

    def thematic_break(self) -> DocxHorizontalRule:
        """Horizontal rule (---, ***, ___)."""
        return DocxHorizontalRule()

    def block_code(self, code: str, info: str | None = None) -> DocxCodeBlock:
        """Fenced or indented code block."""
        language = info.split()[0] if info else None
        return DocxCodeBlock(code=code.rstrip("\n"), language=language)

    def block_quote(self, children: list[Any]) -> DocxElement:
        """Blockquote or admonition."""
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

    def list(self, children: list[Any], ordered: bool, start: int | None = None) -> DocxList:
        """Ordered or unordered list."""
        items = []
        for child in children:
            if isinstance(child, DocxListItem):
                items.append(child)
        return DocxList(ordered=ordered, items=items, start=start or 1)

    def list_item(self, children: list[Any]) -> DocxListItem:
        """List item."""
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

    def table(self, children: list[Any]) -> DocxTable:
        """Table block."""
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

    def table_head(self, children: list[Any]) -> list[DocxTableRow]:
        """Table header section."""
        return self._process_table_rows(children, is_header=True)

    def table_body(self, children: list[Any]) -> list[DocxTableRow]:
        """Table body section."""
        return self._process_table_rows(children, is_header=False)

    def table_row(self, children: list[Any]) -> DocxTableRow:
        """Table row."""
        cells = [c for c in children if isinstance(c, DocxTableCell)]
        return DocxTableRow(cells=cells)

    def table_cell(
        self, children: list[Any], align: str | None = None, head: bool = False
    ) -> DocxTableCell:
        """Table cell."""
        spans = self._flatten_inline(children)
        return DocxTableCell(content=spans, is_header=head)

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
                        DocxTableCell(content=c.content, is_header=True) for c in child.cells
                    ]
                    rows.append(DocxTableRow(cells=cells))
                else:
                    rows.append(child)
        return rows
