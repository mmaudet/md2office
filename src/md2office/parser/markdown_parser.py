"""Markdown parser using mistune tokenizer with custom processing."""

from __future__ import annotations

import re

import mistune

from md2office.core.exceptions import ParserError
from md2office.parser.elements import (
    Document,
    DocxAdmonition,
    DocxBlockquote,
    DocxCodeBlock,
    DocxElement,
    DocxHeading,
    DocxHorizontalRule,
    DocxList,
    DocxListItem,
    DocxParagraph,
    DocxTable,
    DocxTableCell,
    DocxTableRow,
    TextSpan,
)

# Pattern for GitHub-style admonitions
ADMONITION_PATTERN = re.compile(
    r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$", re.IGNORECASE
)


class MarkdownParser:
    """Parser that converts Markdown to DOCX AST elements.

    Uses mistune as a tokenizer and processes tokens into
    intermediate AST representation suitable for DOCX generation.
    """

    def __init__(self) -> None:
        """Initialize the parser with mistune tokenizer."""
        self._md = mistune.create_markdown(plugins=["strikethrough", "table"])

    def parse(self, markdown_text: str) -> Document:
        """Parse Markdown text into a list of DOCX elements.

        Args:
            markdown_text: Markdown source text.

        Returns:
            List of DocxElement objects representing the document.

        Raises:
            ParserError: If parsing fails.
        """
        try:
            # Parse block tokens
            state = self._md.block.state_cls()
            state.process(markdown_text)
            self._md.block.parse(state)

            # Render to populate inline children (modifies tokens in place)
            state.cursor = 0
            state.cursor_max = len(state.tokens)
            self._md.render_state(state)

            # Now process the tokens with children populated
            return self._process_tokens(state.tokens)
        except Exception as e:
            raise ParserError(f"Failed to parse Markdown: {e}") from e

    def _process_tokens(self, tokens: list[dict]) -> list[DocxElement]:
        """Process a list of tokens into DocxElements."""
        elements: list[DocxElement] = []
        for token in tokens:
            element = self._process_token(token)
            if element is not None:
                elements.append(element)
        return elements

    def _process_token(self, token: dict) -> DocxElement | None:
        """Process a single token into a DocxElement."""
        token_type = token.get("type", "")

        if token_type == "heading":
            return self._process_heading(token)
        elif token_type == "paragraph":
            return self._process_paragraph(token)
        elif token_type == "block_text":
            # block_text is used inside list items, treat like paragraph
            return self._process_paragraph(token)
        elif token_type == "block_code":
            return self._process_code_block(token)
        elif token_type == "block_quote":
            return self._process_blockquote(token)
        elif token_type == "list":
            return self._process_list(token)
        elif token_type == "table":
            return self._process_table(token)
        elif token_type == "thematic_break":
            return DocxHorizontalRule()
        elif token_type == "blank_line":
            return None
        else:
            return None

    def _process_heading(self, token: dict) -> DocxHeading:
        """Process a heading token."""
        attrs = token.get("attrs", {})
        level = attrs.get("level", 1)
        children = token.get("children", [])
        content = self._process_inline_tokens(children)
        return DocxHeading(level=level, content=content)

    def _process_paragraph(self, token: dict) -> DocxParagraph:
        """Process a paragraph token."""
        children = token.get("children", [])
        content = self._process_inline_tokens(children)
        return DocxParagraph(content=content)

    def _process_code_block(self, token: dict) -> DocxCodeBlock:
        """Process a code block token."""
        code = token.get("raw", "")
        attrs = token.get("attrs", {})
        info = attrs.get("info", "") or token.get("info", "")
        language = info.split()[0] if info else None
        return DocxCodeBlock(code=code.rstrip("\n"), language=language)

    def _process_blockquote(self, token: dict) -> DocxElement:
        """Process a blockquote token, detecting admonitions."""
        children = token.get("children", [])
        elements = self._process_tokens(children)

        # Check for GitHub-style admonition
        if elements and isinstance(elements[0], DocxParagraph):
            first_para = elements[0]
            if first_para.content:
                # Concatenate all text spans to handle cases where [!NOTE] is split
                # by mistune's link parser into separate tokens
                full_text = "".join(span.text for span in first_para.content)
                match = ADMONITION_PATTERN.match(full_text)
                if match:
                    admonition_type = match.group(1).upper()
                    # Text after [!NOTE] on the same line becomes content
                    content_after_marker = match.group(2).strip()

                    # Build the content: start with text after marker if any,
                    # then add remaining elements
                    if content_after_marker:
                        # Preserve the original formatting from the first paragraph
                        # by finding where the marker ends and keeping the rest
                        marker_end_pos = len(f"[!{admonition_type}]")
                        new_spans = []
                        char_count = 0
                        for span in first_para.content:
                            span_start = char_count
                            span_end = char_count + len(span.text)
                            if span_end > marker_end_pos:
                                # This span contains content after the marker
                                start_in_span = max(0, marker_end_pos - span_start)
                                remaining = span.text[start_in_span:].lstrip()
                                if remaining:
                                    new_spans.append(TextSpan(
                                        text=remaining,
                                        bold=span.bold,
                                        italic=span.italic,
                                        code=span.code,
                                        strikethrough=span.strikethrough,
                                        link=span.link,
                                    ))
                            char_count = span_end
                        if new_spans:
                            elements[0] = DocxParagraph(content=new_spans)
                        else:
                            elements = elements[1:]
                    else:
                        elements = elements[1:]

                    return DocxAdmonition(
                        admonition_type=admonition_type,  # type: ignore[arg-type]
                        title=None,
                        children=elements,
                    )

        return DocxBlockquote(children=elements)

    def _process_list(self, token: dict) -> DocxList:
        """Process a list token."""
        attrs = token.get("attrs", {})
        ordered = attrs.get("ordered", False)
        start = attrs.get("start", 1) or 1
        children = token.get("children", [])

        items: list[DocxListItem] = []
        for child in children:
            if child.get("type") == "list_item":
                item = self._process_list_item(child)
                items.append(item)

        return DocxList(ordered=ordered, items=items, start=start)

    def _process_list_item(self, token: dict) -> DocxListItem:
        """Process a list item token."""
        children = token.get("children", [])
        elements = self._process_tokens(children)

        content: list[TextSpan] = []
        nested: list[DocxElement] = []

        for i, elem in enumerate(elements):
            if i == 0 and isinstance(elem, DocxParagraph):
                content = list(elem.content)
            else:
                nested.append(elem)

        return DocxListItem(content=content, children=nested)

    def _process_table(self, token: dict) -> DocxTable:
        """Process a table token."""
        children = token.get("children", [])
        rows: list[DocxTableRow] = []
        has_header = False

        for child in children:
            child_type = child.get("type", "")
            if child_type == "table_head":
                head_rows = self._process_table_section(child, is_header=True)
                rows.extend(head_rows)
                has_header = True
            elif child_type == "table_body":
                body_rows = self._process_table_section(child, is_header=False)
                rows.extend(body_rows)

        return DocxTable(rows=rows, has_header=has_header)

    def _process_table_section(
        self, token: dict, is_header: bool
    ) -> list[DocxTableRow]:
        """Process table head or body section."""
        children = token.get("children", [])
        rows: list[DocxTableRow] = []

        # Check if children are table_row or directly table_cell
        # (mistune's table_head has direct table_cell children, no table_row wrapper)
        if children and children[0].get("type") == "table_cell":
            # Direct cells - create a single row from them
            cells: list[DocxTableCell] = []
            for child in children:
                if child.get("type") == "table_cell":
                    cell = self._process_table_cell(child, is_header)
                    cells.append(cell)
            if cells:
                rows.append(DocxTableRow(cells=cells))
        else:
            # Wrapped in table_row
            for child in children:
                if child.get("type") == "table_row":
                    row = self._process_table_row(child, is_header)
                    rows.append(row)

        return rows

    def _process_table_row(self, token: dict, is_header: bool) -> DocxTableRow:
        """Process a table row token."""
        children = token.get("children", [])
        cells: list[DocxTableCell] = []

        for child in children:
            if child.get("type") == "table_cell":
                cell = self._process_table_cell(child, is_header)
                cells.append(cell)

        return DocxTableRow(cells=cells)

    def _process_table_cell(self, token: dict, is_header: bool) -> DocxTableCell:
        """Process a table cell token."""
        children = token.get("children", [])
        content = self._process_inline_tokens(children)

        # Check for merge markers
        text = "".join(span.text for span in content).strip()

        # Vertical merge marker (^^) - merge with cell above
        if text == "^^":
            return DocxTableCell(content=[], is_header=is_header, merge_up=True)

        # Horizontal merge marker (>>) - merge with cell to the left
        if text == ">>":
            return DocxTableCell(content=[], is_header=is_header, merge_left=True)

        return DocxTableCell(content=content, is_header=is_header)

    def _process_inline_tokens(self, tokens: list[dict]) -> list[TextSpan]:
        """Process inline tokens into TextSpans."""
        spans: list[TextSpan] = []
        for token in tokens:
            result = self._process_inline_token(token)
            if isinstance(result, list):
                spans.extend(result)
            elif result is not None:
                spans.append(result)
        return spans

    def _process_inline_token(
        self, token: dict
    ) -> TextSpan | list[TextSpan] | None:
        """Process a single inline token."""
        token_type = token.get("type", "")

        if token_type == "text":
            return TextSpan(text=token.get("raw", ""))
        elif token_type == "emphasis":
            children = token.get("children", [])
            spans = self._process_inline_tokens(children)
            return [
                TextSpan(
                    text=s.text,
                    bold=s.bold,
                    italic=True,
                    code=s.code,
                    strikethrough=s.strikethrough,
                    link=s.link,
                )
                for s in spans
            ]
        elif token_type == "strong":
            children = token.get("children", [])
            spans = self._process_inline_tokens(children)
            return [
                TextSpan(
                    text=s.text,
                    bold=True,
                    italic=s.italic,
                    code=s.code,
                    strikethrough=s.strikethrough,
                    link=s.link,
                )
                for s in spans
            ]
        elif token_type == "codespan":
            return TextSpan(text=token.get("raw", ""), code=True)
        elif token_type == "strikethrough":
            children = token.get("children", [])
            spans = self._process_inline_tokens(children)
            return [
                TextSpan(
                    text=s.text,
                    bold=s.bold,
                    italic=s.italic,
                    code=s.code,
                    strikethrough=True,
                    link=s.link,
                )
                for s in spans
            ]
        elif token_type == "link":
            children = token.get("children", [])
            spans = self._process_inline_tokens(children)
            attrs = token.get("attrs", {})
            url = attrs.get("url", "")
            return [
                TextSpan(
                    text=s.text,
                    bold=s.bold,
                    italic=s.italic,
                    code=s.code,
                    strikethrough=s.strikethrough,
                    link=url,
                )
                for s in spans
            ]
        elif token_type == "softbreak":
            return TextSpan(text=" ")
        elif token_type == "linebreak":
            return TextSpan(text="\n")
        else:
            return None

    def parse_file(self, filepath: str) -> Document:
        """Parse Markdown from a file.

        Args:
            filepath: Path to the Markdown file.

        Returns:
            List of DocxElement objects.

        Raises:
            ParserError: If file cannot be read or parsing fails.
        """
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            return self.parse(content)
        except OSError as e:
            raise ParserError(f"Cannot read file: {e}") from e


def parse_markdown(text: str) -> Document:
    """Parse Markdown text into DOCX elements.

    Args:
        text: Markdown source text.

    Returns:
        List of DocxElement objects.
    """
    parser = MarkdownParser()
    return parser.parse(text)
