"""Tests for the Markdown parser."""

from __future__ import annotations

import pytest

from md2office.parser import (
    DocxAdmonition,
    DocxBlockquote,
    DocxCodeBlock,
    DocxHeading,
    DocxHorizontalRule,
    DocxList,
    DocxParagraph,
    DocxTable,
    MarkdownParser,
)


class TestMarkdownParser:
    """Tests for MarkdownParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownParser()

    def test_parse_heading(self):
        """Test parsing headings."""
        md = "# Heading 1\n## Heading 2\n### Heading 3"
        elements = self.parser.parse(md)

        assert len(elements) == 3
        assert isinstance(elements[0], DocxHeading)
        assert elements[0].level == 1
        assert elements[0].content[0].text == "Heading 1"

        assert isinstance(elements[1], DocxHeading)
        assert elements[1].level == 2

        assert isinstance(elements[2], DocxHeading)
        assert elements[2].level == 3

    def test_parse_paragraph(self):
        """Test parsing paragraphs."""
        md = "This is a paragraph.\n\nThis is another paragraph."
        elements = self.parser.parse(md)

        assert len(elements) == 2
        assert all(isinstance(e, DocxParagraph) for e in elements)

    def test_parse_bold_italic(self):
        """Test parsing bold and italic text."""
        md = "This is **bold** and *italic* text."
        elements = self.parser.parse(md)

        assert len(elements) == 1
        para = elements[0]
        assert isinstance(para, DocxParagraph)

        # Check for bold text
        bold_spans = [s for s in para.content if s.bold]
        assert any("bold" in s.text for s in bold_spans)

        # Check for italic text
        italic_spans = [s for s in para.content if s.italic]
        assert any("italic" in s.text for s in italic_spans)

    def test_parse_inline_code(self):
        """Test parsing inline code."""
        md = "Use `print()` to output text."
        elements = self.parser.parse(md)

        assert len(elements) == 1
        para = elements[0]
        code_spans = [s for s in para.content if s.code]
        assert len(code_spans) == 1
        assert code_spans[0].text == "print()"

    def test_parse_code_block(self):
        """Test parsing code blocks."""
        md = "```python\ndef hello():\n    pass\n```"
        elements = self.parser.parse(md)

        assert len(elements) == 1
        code_block = elements[0]
        assert isinstance(code_block, DocxCodeBlock)
        assert code_block.language == "python"
        assert "def hello()" in code_block.code

    def test_parse_unordered_list(self):
        """Test parsing unordered lists."""
        md = "- Item 1\n- Item 2\n- Item 3"
        elements = self.parser.parse(md)

        assert len(elements) == 1
        lst = elements[0]
        assert isinstance(lst, DocxList)
        assert not lst.ordered
        assert len(lst.items) == 3

    def test_parse_ordered_list(self):
        """Test parsing ordered lists."""
        md = "1. First\n2. Second\n3. Third"
        elements = self.parser.parse(md)

        assert len(elements) == 1
        lst = elements[0]
        assert isinstance(lst, DocxList)
        assert lst.ordered
        assert len(lst.items) == 3

    def test_parse_table(self):
        """Test parsing tables."""
        md = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
        elements = self.parser.parse(md)

        assert len(elements) == 1
        table = elements[0]
        assert isinstance(table, DocxTable)
        assert len(table.rows) == 3  # Header + 2 data rows
        assert table.has_header

    def test_parse_blockquote(self):
        """Test parsing blockquotes."""
        md = "> This is a quote."
        elements = self.parser.parse(md)

        assert len(elements) == 1
        quote = elements[0]
        assert isinstance(quote, DocxBlockquote)
        assert len(quote.children) == 1

    def test_parse_admonition_note(self):
        """Test parsing NOTE admonition."""
        md = "> [!NOTE]\n> This is a note."
        elements = self.parser.parse(md)

        assert len(elements) == 1
        admonition = elements[0]
        assert isinstance(admonition, DocxAdmonition)
        assert admonition.admonition_type == "NOTE"

    def test_parse_admonition_warning(self):
        """Test parsing WARNING admonition."""
        md = "> [!WARNING]\n> This is a warning."
        elements = self.parser.parse(md)

        assert len(elements) == 1
        admonition = elements[0]
        assert isinstance(admonition, DocxAdmonition)
        assert admonition.admonition_type == "WARNING"

    def test_parse_horizontal_rule(self):
        """Test parsing horizontal rules."""
        md = "Text above\n\n---\n\nText below"
        elements = self.parser.parse(md)

        assert len(elements) == 3
        assert isinstance(elements[1], DocxHorizontalRule)

    def test_parse_link(self):
        """Test parsing links."""
        md = "Click [here](https://example.com) for more."
        elements = self.parser.parse(md)

        assert len(elements) == 1
        para = elements[0]
        link_spans = [s for s in para.content if s.link]
        assert len(link_spans) == 1
        assert link_spans[0].link == "https://example.com"
        assert link_spans[0].text == "here"

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        elements = self.parser.parse("")
        assert elements == []

    def test_parse_complex_document(self, sample_markdown):
        """Test parsing a complex document with multiple elements."""
        elements = self.parser.parse(sample_markdown)
        assert len(elements) > 0

        # Check for various element types
        element_types = {type(e) for e in elements}
        assert DocxHeading in element_types
        assert DocxParagraph in element_types
        assert DocxList in element_types
        assert DocxCodeBlock in element_types
        assert DocxTable in element_types
