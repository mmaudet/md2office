"""Table construction for DOCX documents."""

from __future__ import annotations

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.table import Table, _Cell

from md2office.builder.style_mapper import StyleMapper
from md2office.parser.elements import DocxTable, TextSpan


class TableBuilder:
    """Builds Word tables from DocxTable elements."""

    def __init__(self, document: Document, style_mapper: StyleMapper) -> None:
        """Initialize table builder.

        Args:
            document: Word document to add tables to.
            style_mapper: Style mapper for table styles.
        """
        self._document = document
        self._style_mapper = style_mapper

    def build(self, table_element: DocxTable) -> Table:
        """Build a Word table from a DocxTable element.

        Args:
            table_element: DocxTable element to convert.

        Returns:
            Word Table object.
        """
        if not table_element.rows:
            return self._document.add_table(rows=0, cols=0)

        num_rows = len(table_element.rows)
        num_cols = max(len(row.cells) for row in table_element.rows)

        # Create table
        table = self._document.add_table(rows=num_rows, cols=num_cols)

        # Apply table style
        try:
            table.style = self._style_mapper.table_style()
        except KeyError:
            pass  # Style not found, use default

        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Get table formatting config
        config = self._style_mapper.table_config()

        # Fill table cells
        for row_idx, row in enumerate(table_element.rows):
            is_header_row = row_idx == 0 and table_element.has_header

            for col_idx, cell in enumerate(row.cells):
                if col_idx >= num_cols:
                    break

                table_cell = table.rows[row_idx].cells[col_idx]
                self._fill_cell(table_cell, cell.content, is_header_row, config)

            # Apply alternating row colors
            if not is_header_row and config.get("alternating_rows", False):
                if row_idx % 2 == 0:  # Even rows (0-indexed, so 0, 2, 4...)
                    self._set_row_bg_color(table.rows[row_idx], config.get("alt_row_bg", "D9E2F3"))

        return table

    def _fill_cell(
        self,
        cell: _Cell,
        content: list[TextSpan],
        is_header: bool,
        config: dict,
    ) -> None:
        """Fill a table cell with content.

        Args:
            cell: Word table cell.
            content: List of text spans.
            is_header: Whether this is a header cell.
            config: Table formatting configuration.
        """
        # Clear existing content
        cell.text = ""
        paragraph = cell.paragraphs[0]

        # Add content with formatting
        for span in content:
            run = paragraph.add_run(span.text)
            run.bold = span.bold or is_header
            run.italic = span.italic
            if span.code:
                run.font.name = "Consolas"
                run.font.size = Pt(10)

        # Header cell formatting
        if is_header:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            header_bg = config.get("header_bg", "4472C4")
            header_text = config.get("header_text", "FFFFFF")
            self._set_cell_bg_color(cell, header_bg)
            for run in paragraph.runs:
                run.font.color.rgb = RGBColor.from_string(header_text)

    def _set_cell_bg_color(self, cell: _Cell, color: str) -> None:
        """Set background color of a cell.

        Args:
            cell: Word table cell.
            color: Hex color string (without #).
        """
        tc = cell._tc
        tc_pr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), color)
        tc_pr.append(shd)

    def _set_row_bg_color(self, row, color: str) -> None:
        """Set background color for all cells in a row.

        Args:
            row: Word table row.
            color: Hex color string (without #).
        """
        for cell in row.cells:
            self._set_cell_bg_color(cell, color)
