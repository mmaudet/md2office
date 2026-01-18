"""Admonition/callout construction for DOCX documents."""

from __future__ import annotations

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table

from md2office.builder.style_mapper import StyleMapper
from md2office.parser.elements import DocxAdmonition, DocxParagraph, TextSpan


class AdmonitionBuilder:
    """Builds Word admonitions (callouts) as styled tables."""

    # Admonition icons/emoji
    ICONS = {
        "NOTE": "\u2139",  # Information source
        "TIP": "\U0001F4A1",  # Light bulb
        "IMPORTANT": "\u2757",  # Exclamation mark
        "WARNING": "\u26A0",  # Warning sign
        "CAUTION": "\U0001F6D1",  # Stop sign
    }

    def __init__(self, document: Document, style_mapper: StyleMapper) -> None:
        """Initialize admonition builder.

        Args:
            document: Word document to add admonitions to.
            style_mapper: Style mapper for admonition configuration.
        """
        self._document = document
        self._style_mapper = style_mapper

    def build(self, admonition: DocxAdmonition) -> Table:
        """Build a Word table representing an admonition.

        Args:
            admonition: DocxAdmonition element to convert.

        Returns:
            Word Table object styled as an admonition.
        """
        config = self._style_mapper.admonition_config(admonition.admonition_type)

        # Create a single-row, two-column table
        table = self._document.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        # Set column widths
        table.columns[0].width = Inches(0.5)  # Icon column
        table.columns[1].width = Inches(5.5)  # Content column

        # Get the row and cells
        row = table.rows[0]
        icon_cell = row.cells[0]
        content_cell = row.cells[1]

        # Style the icon cell
        self._build_icon_cell(icon_cell, admonition.admonition_type, config)

        # Style the content cell
        self._build_content_cell(content_cell, admonition, config)

        # Apply background color to both cells
        bg_color = config.get("bg", "DDF4FF")
        self._set_cell_bg_color(icon_cell, bg_color)
        self._set_cell_bg_color(content_cell, bg_color)

        # Apply border color
        border_color = config.get("color", "0969DA")
        self._set_table_borders(table, border_color)

        return table

    def _build_icon_cell(self, cell, admonition_type: str, config: dict) -> None:
        """Build the icon cell.

        Args:
            cell: Word table cell for the icon.
            admonition_type: Type of admonition.
            config: Admonition configuration.
        """
        cell.text = ""
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add icon
        icon = self.ICONS.get(admonition_type, "\u2139")
        run = paragraph.add_run(icon)
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor.from_string(config.get("color", "0969DA"))

    def _build_content_cell(self, cell, admonition: DocxAdmonition, config: dict) -> None:
        """Build the content cell.

        Args:
            cell: Word table cell for content.
            admonition: Admonition element.
            config: Admonition configuration.
        """
        cell.text = ""

        # Add title
        title = admonition.title or admonition.admonition_type.capitalize()
        title_para = cell.paragraphs[0]
        title_run = title_para.add_run(title)
        title_run.bold = True
        title_run.font.size = Pt(11)
        title_run.font.color.rgb = RGBColor.from_string(config.get("color", "0969DA"))

        # Add content from children
        for child in admonition.children:
            if isinstance(child, DocxParagraph):
                para = cell.add_paragraph()
                self._add_text_spans(para, child.content)

    def _add_text_spans(self, paragraph, spans: list[TextSpan]) -> None:
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

    def _set_cell_bg_color(self, cell, color: str) -> None:
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

    def _set_table_borders(self, table: Table, color: str) -> None:
        """Set colored left border on the table.

        Args:
            table: Word table.
            color: Hex color string (without #).
        """
        tbl = table._tbl
        tbl_pr = tbl.tblPr if tbl.tblPr is not None else OxmlElement("w:tblPr")

        tbl_borders = OxmlElement("w:tblBorders")

        # Only add left border (callout style)
        left = OxmlElement("w:left")
        left.set(qn("w:val"), "single")
        left.set(qn("w:sz"), "24")  # 3pt border
        left.set(qn("w:color"), color)
        tbl_borders.append(left)

        # Remove other borders
        for border_name in ["top", "right", "bottom", "insideH", "insideV"]:
            border = OxmlElement(f"w:{border_name}")
            border.set(qn("w:val"), "nil")
            tbl_borders.append(border)

        tbl_pr.append(tbl_borders)
        if tbl.tblPr is None:
            tbl.insert(0, tbl_pr)
