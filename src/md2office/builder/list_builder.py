"""List construction for DOCX documents."""

from __future__ import annotations

from docx import Document
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

from md2office.builder.style_mapper import StyleMapper
from md2office.parser.elements import DocxList, DocxListItem, TextSpan


class ListBuilder:
    """Builds Word lists from DocxList elements."""

    def __init__(self, document: Document, style_mapper: StyleMapper) -> None:
        """Initialize list builder.

        Args:
            document: Word document to add lists to.
            style_mapper: Style mapper for list styles.
        """
        self._document = document
        self._style_mapper = style_mapper

    def build(self, list_element: DocxList, level: int = 0) -> list[Paragraph]:
        """Build Word list paragraphs from a DocxList element.

        Args:
            list_element: DocxList element to convert.
            level: Nesting level for indentation.

        Returns:
            List of Word Paragraph objects.
        """
        paragraphs: list[Paragraph] = []
        style_name = self._style_mapper.list_style(list_element.ordered)

        for idx, item in enumerate(list_element.items):
            para = self._build_list_item(
                item,
                list_element.ordered,
                level,
                style_name,
                idx + list_element.start,
            )
            paragraphs.append(para)

            # Handle nested content
            for child in item.children:
                if isinstance(child, DocxList):
                    paragraphs.extend(self.build(child, level + 1))

        return paragraphs

    def _build_list_item(
        self,
        item: DocxListItem,
        ordered: bool,
        level: int,
        style_name: str,
        number: int,
    ) -> Paragraph:
        """Build a single list item paragraph.

        Args:
            item: List item element.
            ordered: Whether parent list is ordered.
            level: Nesting level.
            style_name: Word style name to use.
            number: Item number (for ordered lists).

        Returns:
            Word Paragraph object.
        """
        paragraph = self._document.add_paragraph()

        # Try to apply list style
        try:
            paragraph.style = style_name
        except KeyError:
            pass  # Style not found, use default

        # Set indentation based on level
        indent = Inches(0.5 * level)
        paragraph.paragraph_format.left_indent = indent

        # Add bullet/number prefix if style doesn't handle it
        if not self._style_has_numbering(style_name):
            prefix = f"{number}. " if ordered else "• "
            run = paragraph.add_run(prefix)
            run.bold = False

        # Add content with formatting
        self._add_text_spans(paragraph, item.content)

        return paragraph

    def _add_text_spans(self, paragraph: Paragraph, spans: list[TextSpan]) -> None:
        """Add text spans to a paragraph.

        Args:
            paragraph: Word paragraph.
            spans: List of text spans to add.
        """
        for span in spans:
            run = paragraph.add_run(span.text)
            run.bold = span.bold
            run.italic = span.italic

            if span.code:
                run.font.name = "Consolas"
                run.font.size = Pt(10)

            if span.strikethrough:
                run.font.strike = True

            if span.link:
                # Word doesn't support hyperlinks directly in runs
                # We'll add the URL in parentheses for now
                # A more complete implementation would use oxml
                run.underline = True

    def _style_has_numbering(self, style_name: str) -> bool:
        """Check if a style has built-in numbering.

        Args:
            style_name: Name of the style.

        Returns:
            True if style handles numbering automatically.
        """
        # Styles that typically handle their own numbering
        numbered_styles = {
            "List Bullet",
            "List Number",
            "List Bullet 2",
            "List Number 2",
            "List Bullet 3",
            "List Number 3",
        }
        return style_name in numbered_styles
