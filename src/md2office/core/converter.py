"""Main converter orchestrating the MD to DOCX pipeline."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO

from md2office.builder.docx_builder import DocxBuilder
from md2office.core.config import StylesConfig, get_config, load_styles_mapping
from md2office.parser.markdown_parser import MarkdownParser
from md2office.template.engine import TemplateEngine
from md2office.template.storage import TemplateStorage
from md2office.utils.helpers import normalize_line_endings


class Converter:
    """Orchestrates the Markdown to DOCX conversion pipeline.

    Combines parsing, template processing, and document building
    into a single conversion workflow.
    """

    def __init__(
        self,
        template_name: str | None = None,
        template_path: Path | str | None = None,
        styles_config: StylesConfig | None = None,
        variables: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the converter.

        Args:
            template_name: Name of template from storage to use.
            template_path: Direct path to a template file.
                          Takes precedence over template_name.
            styles_config: Style mapping configuration.
            variables: Default variables for template injection.
        """
        self._template_name = template_name
        self._template_path = Path(template_path) if template_path else None
        self._styles_config = styles_config or load_styles_mapping()
        self._variables = variables or {}

        # Initialize components
        self._parser = MarkdownParser()
        self._storage = TemplateStorage()
        self._template_engine = TemplateEngine(self._storage)

    def convert(
        self,
        markdown: str,
        output_path: Path | str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> bytes | Path:
        """Convert Markdown text to DOCX.

        Args:
            markdown: Markdown source text.
            output_path: Optional path to save the document.
                        If provided, saves and returns the path.
                        If not, returns document as bytes.
            variables: Additional variables for template injection.
                      Merged with default variables (overrides them).

        Returns:
            Path to saved document, or bytes if no output_path.

        Raises:
            Md2OfficeError: If conversion fails.
        """
        # Merge variables
        all_variables = {**self._variables, **(variables or {})}

        # Normalize line endings
        markdown = normalize_line_endings(markdown)

        # Pre-process markdown with Jinja2 if it contains variables
        if all_variables and "{{" in markdown:
            markdown = self._template_engine.render_jinja_string(markdown, all_variables)

        # Parse markdown to AST
        elements = self._parser.parse(markdown)

        # Determine template path
        template_path = self._get_template_path()

        # Build DOCX
        builder = DocxBuilder(
            template_path=template_path,
            styles_config=self._styles_config,
        )

        if output_path:
            output_path = Path(output_path)
            builder.build_to_file(elements, output_path)

            # Inject variables if template was used
            if template_path and all_variables:
                from docx import Document

                doc = Document(output_path)
                self._template_engine.inject_variables(doc, all_variables)
                doc.save(output_path)

            return output_path
        else:
            doc = builder.build(elements)

            # Inject variables if template was used
            if template_path and all_variables:
                self._template_engine.inject_variables(doc, all_variables)

            # Save to bytes
            buffer = BytesIO()
            doc.save(buffer)
            return buffer.getvalue()

    def convert_file(
        self,
        input_path: Path | str,
        output_path: Path | str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> bytes | Path:
        """Convert a Markdown file to DOCX.

        Args:
            input_path: Path to the Markdown file.
            output_path: Optional path for the output DOCX.
                        Defaults to input path with .docx extension.
            variables: Variables for template injection.

        Returns:
            Path to saved document, or bytes if no output_path.
        """
        input_path = Path(input_path)

        with open(input_path, encoding="utf-8") as f:
            markdown = f.read()

        # Default output path
        if output_path is None:
            output_path = input_path.with_suffix(".docx")

        return self.convert(markdown, output_path, variables)

    def convert_to_stream(
        self,
        markdown: str,
        stream: BinaryIO,
        variables: dict[str, Any] | None = None,
    ) -> None:
        """Convert Markdown and write to a stream.

        Args:
            markdown: Markdown source text.
            stream: Binary stream to write to.
            variables: Variables for template injection.
        """
        doc_bytes = self.convert(markdown, variables=variables)
        assert isinstance(doc_bytes, bytes)
        stream.write(doc_bytes)

    def _get_template_path(self) -> Path | None:
        """Get the template path to use.

        Returns:
            Path to template, or None if no template.
        """
        # Direct path takes precedence
        if self._template_path and self._template_path.exists():
            return self._template_path

        # Try template name from storage
        if self._template_name:
            if self._storage.template_exists(self._template_name):
                return self._storage.get_template_path(self._template_name)

        # Try default template
        config = get_config()
        if self._storage.template_exists(config.default_template):
            return self._storage.get_template_path(config.default_template)

        return None


def convert(
    input_path: Path | str,
    output_path: Path | str | None = None,
    template: str | None = None,
    variables: dict[str, Any] | None = None,
) -> Path:
    """Convenience function for quick conversions.

    Args:
        input_path: Path to the Markdown file.
        output_path: Optional output path.
        template: Optional template name.
        variables: Optional variables dictionary.

    Returns:
        Path to the generated DOCX file.
    """
    converter = Converter(template_name=template, variables=variables)
    result = converter.convert_file(input_path, output_path, variables)
    assert isinstance(result, Path)
    return result
