"""Tests for the DOCX builder."""

from __future__ import annotations

from md2office.builder import DocxBuilder
from md2office.parser import (
    DocxCodeBlock,
    DocxHeading,
    DocxList,
    DocxListItem,
    DocxParagraph,
    DocxTable,
    DocxTableCell,
    DocxTableRow,
    MarkdownParser,
    TextSpan,
)


class TestDocxBuilder:
    """Tests for DocxBuilder class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.builder = DocxBuilder()
        self.parser = MarkdownParser()

    def test_build_empty_document(self):
        """Test building an empty document."""
        doc = self.builder.build([])
        assert doc is not None
        assert len(doc.paragraphs) == 0

    def test_build_heading(self):
        """Test building a heading."""
        elements = [
            DocxHeading(level=1, content=[TextSpan(text="Test Heading")])
        ]
        doc = self.builder.build(elements)
        assert len(doc.paragraphs) == 1
        assert doc.paragraphs[0].text == "Test Heading"

    def test_build_paragraph(self):
        """Test building a paragraph."""
        elements = [
            DocxParagraph(content=[TextSpan(text="This is a test paragraph.")])
        ]
        doc = self.builder.build(elements)
        assert len(doc.paragraphs) == 1
        assert doc.paragraphs[0].text == "This is a test paragraph."

    def test_build_formatted_text(self):
        """Test building text with formatting."""
        elements = [
            DocxParagraph(content=[
                TextSpan(text="Normal "),
                TextSpan(text="bold", bold=True),
                TextSpan(text=" and "),
                TextSpan(text="italic", italic=True),
            ])
        ]
        doc = self.builder.build(elements)
        assert len(doc.paragraphs) == 1
        runs = doc.paragraphs[0].runs
        assert any(r.bold for r in runs)
        assert any(r.italic for r in runs)

    def test_build_code_block(self):
        """Test building a code block."""
        elements = [
            DocxCodeBlock(code="print('hello')", language="python")
        ]
        doc = self.builder.build(elements)
        assert len(doc.paragraphs) == 1
        assert "print" in doc.paragraphs[0].text

    def test_build_list(self):
        """Test building a list."""
        elements = [
            DocxList(
                ordered=False,
                items=[
                    DocxListItem(content=[TextSpan(text="Item 1")]),
                    DocxListItem(content=[TextSpan(text="Item 2")]),
                ],
            )
        ]
        doc = self.builder.build(elements)
        # Lists create multiple paragraphs
        assert len(doc.paragraphs) >= 2

    def test_build_table(self):
        """Test building a table."""
        elements = [
            DocxTable(
                rows=[
                    DocxTableRow(cells=[
                        DocxTableCell(content=[TextSpan(text="A")], is_header=True),
                        DocxTableCell(content=[TextSpan(text="B")], is_header=True),
                    ]),
                    DocxTableRow(cells=[
                        DocxTableCell(content=[TextSpan(text="1")]),
                        DocxTableCell(content=[TextSpan(text="2")]),
                    ]),
                ],
                has_header=True,
            )
        ]
        doc = self.builder.build(elements)
        assert len(doc.tables) == 1
        assert len(doc.tables[0].rows) == 2
        assert len(doc.tables[0].columns) == 2

    def test_build_to_bytes(self):
        """Test building document to bytes."""
        elements = [
            DocxParagraph(content=[TextSpan(text="Test")])
        ]
        doc_bytes = self.builder.build_to_bytes(elements)
        assert isinstance(doc_bytes, bytes)
        assert len(doc_bytes) > 0
        # Check for DOCX magic bytes (PK zip header)
        assert doc_bytes[:2] == b"PK"

    def test_build_to_file(self, temp_dir):
        """Test building document to file."""
        elements = [
            DocxParagraph(content=[TextSpan(text="Test")])
        ]
        output_path = temp_dir / "test.docx"
        result_path = self.builder.build_to_file(elements, output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_build_complex_document(self, sample_markdown):
        """Test building a complex document from parsed markdown."""
        elements = self.parser.parse(sample_markdown)
        doc = self.builder.build(elements)

        assert doc is not None
        assert len(doc.paragraphs) > 0
        # Should have at least one table
        assert len(doc.tables) >= 1
