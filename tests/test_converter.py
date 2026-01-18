"""Tests for the converter orchestrator."""

from __future__ import annotations

from pathlib import Path

from md2office.core.converter import Converter, convert


class TestConverter:
    """Tests for Converter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.converter = Converter()

    def test_convert_simple_markdown(self):
        """Test converting simple markdown to bytes."""
        md = "# Hello World\n\nThis is a test."
        result = self.converter.convert(md)

        assert isinstance(result, bytes)
        assert len(result) > 0
        # Check for DOCX magic bytes
        assert result[:2] == b"PK"

    def test_convert_to_file(self, temp_dir, simple_markdown):
        """Test converting markdown to a file."""
        input_path = temp_dir / "test.md"
        input_path.write_text(simple_markdown)

        output_path = temp_dir / "output.docx"
        result = self.converter.convert_file(input_path, output_path)

        assert isinstance(result, Path)
        assert result.exists()
        assert result.stat().st_size > 0

    def test_convert_with_variables(self):
        """Test converting with template variables."""
        md = "# {{title}}\n\nAuthor: {{author}}"
        variables = {"title": "My Document", "author": "John Doe"}

        result = self.converter.convert(md, variables=variables)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_convert_auto_output_path(self, temp_dir, simple_markdown):
        """Test automatic output path generation."""
        input_path = temp_dir / "document.md"
        input_path.write_text(simple_markdown)

        result = self.converter.convert_file(input_path)

        assert isinstance(result, Path)
        assert result.name == "document.docx"
        assert result.exists()


class TestConvertFunction:
    """Tests for the convert convenience function."""

    def test_convert_function(self, temp_dir, simple_markdown):
        """Test the convert convenience function."""
        input_path = temp_dir / "test.md"
        input_path.write_text(simple_markdown)

        output_path = temp_dir / "output.docx"
        result = convert(input_path, output_path)

        assert isinstance(result, Path)
        assert result.exists()
