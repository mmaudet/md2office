"""Maps Markdown elements to Word styles."""

from __future__ import annotations

from docx import Document
from docx.styles.style import BaseStyle

from md2office.core.config import StylesConfig


class StyleMapper:
    """Maps Markdown element types to Word style names."""

    def __init__(self, config: StylesConfig, document: Document) -> None:
        """Initialize style mapper.

        Args:
            config: Style configuration.
            document: Word document to check for available styles.
        """
        self._config = config
        self._document = document
        self._available_styles = self._get_available_styles()

    def _get_available_styles(self) -> set[str]:
        """Get set of style names available in the document."""
        styles = set()
        for style in self._document.styles:
            if isinstance(style, BaseStyle) and style.name:
                styles.add(style.name)
        return styles

    def _get_style(self, name: str, fallback: str = "Normal") -> str:
        """Get style name, falling back if not available.

        Args:
            name: Desired style name.
            fallback: Fallback style if not found.

        Returns:
            Style name to use.
        """
        if name in self._available_styles:
            return name
        if fallback in self._available_styles:
            return fallback
        return "Normal"

    def heading_style(self, level: int) -> str:
        """Get style for heading level.

        Args:
            level: Heading level (1-6).

        Returns:
            Word style name for the heading.
        """
        key = f"h{level}"
        default = f"Heading {level}"
        style_name = self._config.headings.get(key, default)
        return self._get_style(style_name, "Normal")

    def paragraph_style(self, style_type: str = "normal") -> str:
        """Get style for paragraph.

        Args:
            style_type: Type of paragraph ("normal", "quote").

        Returns:
            Word style name for the paragraph.
        """
        style_name = self._config.paragraph.get(style_type, "Normal")
        return self._get_style(style_name, "Normal")

    def code_style(self, block: bool = False) -> str:
        """Get style for code.

        Args:
            block: Whether this is a code block (vs inline).

        Returns:
            Word style name for the code.
        """
        key = "block" if block else "inline"
        style_name = self._config.code.get(key, "Normal")
        return self._get_style(style_name, "Normal")

    def list_style(self, ordered: bool = False) -> str:
        """Get style for list.

        Args:
            ordered: Whether this is an ordered list.

        Returns:
            Word style name for the list.
        """
        key = "number" if ordered else "bullet"
        style_name = self._config.list_styles.get(key, "List Bullet")
        return self._get_style(style_name, "Normal")

    def table_style(self) -> str:
        """Get style for table.

        Returns:
            Word style name for the table.
        """
        style_name = self._config.table.get("style", "Table Grid")
        return self._get_style(style_name, "Table Grid")

    def table_config(self) -> dict:
        """Get table formatting configuration.

        Returns:
            Dictionary with table formatting options.
        """
        return {
            "header_bg": self._config.table.get("header_bg", "4472C4"),
            "header_text": self._config.table.get("header_text", "FFFFFF"),
            "alternating_rows": self._config.table.get("alternating_rows", True),
            "alt_row_bg": self._config.table.get("alt_row_bg", "D9E2F3"),
        }

    def admonition_config(self, admonition_type: str) -> dict:
        """Get admonition formatting configuration.

        Args:
            admonition_type: Type of admonition (NOTE, WARNING, etc.).

        Returns:
            Dictionary with admonition formatting options.
        """
        defaults = {
            "NOTE": {"icon": "i", "color": "0969DA", "bg": "DDF4FF"},
            "TIP": {"icon": "tip", "color": "1A7F37", "bg": "DCFFE4"},
            "IMPORTANT": {"icon": "!", "color": "8250DF", "bg": "FBEFFF"},
            "WARNING": {"icon": "warn", "color": "9A6700", "bg": "FFF8C5"},
            "CAUTION": {"icon": "x", "color": "CF222E", "bg": "FFEBE9"},
        }
        return self._config.admonitions.get(
            admonition_type, defaults.get(admonition_type, defaults["NOTE"])
        )
