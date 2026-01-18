"""Generate default DOCX templates."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from md2office.utils.helpers import ensure_dir


def create_default_template(output_path: Path | str | None = None) -> Path:
    """Create a default DOCX template with standard styles.

    Args:
        output_path: Path to save the template.
                    Defaults to templates/default.docx

    Returns:
        Path to the created template.
    """
    if output_path is None:
        output_path = Path("templates/default.docx")
    else:
        output_path = Path(output_path)

    ensure_dir(output_path.parent)

    doc = Document()

    # Configure document margins
    for section in doc.sections:
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)

    # Define heading styles
    _configure_heading_styles(doc)

    # Define code styles
    _configure_code_styles(doc)

    # Define list styles
    _configure_list_styles(doc)

    # Define quote style
    _configure_quote_style(doc)

    # Add header with placeholder
    _configure_header(doc)

    # Add footer with page number
    _configure_footer(doc)

    # Save the template
    doc.save(output_path)

    return output_path


def _configure_heading_styles(doc: Document) -> None:
    """Configure heading styles."""
    styles = doc.styles

    # Heading configurations: (level, size, bold, color)
    heading_config = [
        (1, 24, True, "2F5496"),
        (2, 18, True, "2F5496"),
        (3, 14, True, "2F5496"),
        (4, 12, True, "2F5496"),
        (5, 11, True, "2F5496"),
        (6, 11, False, "2F5496"),
    ]

    for level, size, bold, color in heading_config:
        style_name = f"Heading {level}"
        try:
            style = styles[style_name]
        except KeyError:
            style = styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)

        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(12 if level == 1 else 6)
        style.paragraph_format.space_after = Pt(6)


def _configure_code_styles(doc: Document) -> None:
    """Configure code styles."""
    styles = doc.styles

    # Inline code character style
    try:
        code_char = styles["Code Char"]
    except KeyError:
        code_char = styles.add_style("Code Char", WD_STYLE_TYPE.CHARACTER)

    code_char.font.name = "Consolas"
    code_char.font.size = Pt(10)

    # Code block paragraph style
    try:
        code_block = styles["Code Block"]
    except KeyError:
        code_block = styles.add_style("Code Block", WD_STYLE_TYPE.PARAGRAPH)

    code_block.font.name = "Consolas"
    code_block.font.size = Pt(10)
    code_block.paragraph_format.left_indent = Inches(0.5)
    code_block.paragraph_format.space_before = Pt(6)
    code_block.paragraph_format.space_after = Pt(6)


def _configure_list_styles(doc: Document) -> None:
    """Configure list styles."""
    styles = doc.styles

    # List Bullet style
    try:
        list_bullet = styles["List Bullet"]
    except KeyError:
        list_bullet = styles.add_style("List Bullet", WD_STYLE_TYPE.PARAGRAPH)

    list_bullet.paragraph_format.left_indent = Inches(0.5)
    list_bullet.paragraph_format.space_after = Pt(3)

    # List Number style
    try:
        list_number = styles["List Number"]
    except KeyError:
        list_number = styles.add_style("List Number", WD_STYLE_TYPE.PARAGRAPH)

    list_number.paragraph_format.left_indent = Inches(0.5)
    list_number.paragraph_format.space_after = Pt(3)


def _configure_quote_style(doc: Document) -> None:
    """Configure blockquote style."""
    styles = doc.styles

    try:
        quote = styles["Quote"]
    except KeyError:
        quote = styles.add_style("Quote", WD_STYLE_TYPE.PARAGRAPH)

    quote.font.italic = True
    quote.font.color.rgb = RGBColor.from_string("666666")
    quote.paragraph_format.left_indent = Inches(0.5)
    quote.paragraph_format.space_before = Pt(6)
    quote.paragraph_format.space_after = Pt(6)


def _configure_header(doc: Document) -> None:
    """Configure document header."""
    section = doc.sections[0]
    header = section.header
    paragraph = header.paragraphs[0]
    paragraph.text = "{{title}}"
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def _configure_footer(doc: Document) -> None:
    """Configure document footer with page number."""
    section = doc.sections[0]
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Add page number field
    run = paragraph.add_run("Page ")
    _add_page_number_field(paragraph)


def _add_page_number_field(paragraph) -> None:
    """Add a page number field to a paragraph."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    run = paragraph.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")

    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"

    fld_char_separate = OxmlElement("w:fldChar")
    fld_char_separate.set(qn("w:fldCharType"), "separate")

    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")

    run._r.append(fld_char_begin)
    run._r.append(instr_text)
    run._r.append(fld_char_separate)
    run._r.append(fld_char_end)


if __name__ == "__main__":
    path = create_default_template()
    print(f"Created default template: {path}")
