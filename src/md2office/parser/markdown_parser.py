"""Markdown parser using mistune with custom DOCX renderer."""

from __future__ import annotations

import mistune

from md2office.core.exceptions import ParserError
from md2office.parser.elements import Document, DocxElement
from md2office.parser.renderer import DocxRenderer


class MarkdownParser:
    """Parser that converts Markdown to DOCX AST elements.

    Uses mistune with a custom renderer to produce intermediate AST
    representation suitable for DOCX generation.
    """

    def __init__(self) -> None:
        """Initialize the parser with mistune and custom renderer."""
        self._renderer = DocxRenderer()
        self._parser = mistune.create_markdown(
            renderer=self._renderer,
            plugins=["strikethrough", "table"],
        )

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
            result = self._parser(markdown_text)
            # The parser returns the result from the renderer
            # We need to flatten it into a list of elements
            if isinstance(result, list):
                return self._flatten_result(result)
            elif isinstance(result, DocxElement):
                return [result]
            elif result is None:
                return []
            else:
                # Mistune returns string for HTML renderer, but we return elements
                return self._flatten_result(result) if isinstance(result, list) else []
        except Exception as e:
            raise ParserError(f"Failed to parse Markdown: {e}") from e

    def _flatten_result(self, items: list) -> Document:
        """Flatten nested results into a document."""
        result: Document = []
        for item in items:
            if isinstance(item, DocxElement):
                result.append(item)
            elif isinstance(item, list):
                result.extend(self._flatten_result(item))
            elif item is None:
                pass
        return result

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


# Convenience function for simple parsing
def parse_markdown(text: str) -> Document:
    """Parse Markdown text into DOCX elements.

    Args:
        text: Markdown source text.

    Returns:
        List of DocxElement objects.
    """
    parser = MarkdownParser()
    return parser.parse(text)
