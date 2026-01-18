"""Template storage and management."""

from __future__ import annotations

import shutil
from pathlib import Path

from md2office.core.config import get_config
from md2office.core.exceptions import StorageError, TemplateError
from md2office.utils.helpers import ensure_dir, get_file_hash, sanitize_filename


class TemplateStorage:
    """Manages DOCX template storage and retrieval."""

    def __init__(self, templates_dir: Path | str | None = None) -> None:
        """Initialize template storage.

        Args:
            templates_dir: Directory containing templates.
                          Defaults to config setting.
        """
        if templates_dir:
            self._templates_dir = Path(templates_dir)
        else:
            config = get_config()
            self._templates_dir = Path(config.storage.templates_dir)

        ensure_dir(self._templates_dir)

    @property
    def templates_dir(self) -> Path:
        """Get the templates directory path."""
        return self._templates_dir

    def list_templates(self) -> list[dict]:
        """List all available templates.

        Returns:
            List of template info dictionaries with name, path, and size.
        """
        templates = []
        for path in self._templates_dir.glob("*.docx"):
            templates.append(
                {
                    "name": path.stem,
                    "path": str(path),
                    "size": path.stat().st_size,
                    "modified": path.stat().st_mtime,
                }
            )
        return sorted(templates, key=lambda x: x["name"])

    def get_template_path(self, name: str) -> Path:
        """Get the path to a template file.

        Args:
            name: Template name (without .docx extension).

        Returns:
            Path to the template file.

        Raises:
            TemplateError: If template not found.
        """
        # Handle both "name" and "name.docx"
        if not name.endswith(".docx"):
            name = f"{name}.docx"

        path = self._templates_dir / name
        if not path.exists():
            raise TemplateError(f"Template not found: {name}")

        return path

    def template_exists(self, name: str) -> bool:
        """Check if a template exists.

        Args:
            name: Template name (without .docx extension).

        Returns:
            True if template exists.
        """
        if not name.endswith(".docx"):
            name = f"{name}.docx"
        return (self._templates_dir / name).exists()

    def add_template(
        self,
        source_path: Path | str,
        name: str | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Add a template to storage.

        Args:
            source_path: Path to the source DOCX file.
            name: Optional name for the template.
                 Defaults to source filename.
            overwrite: Whether to overwrite existing template.

        Returns:
            Path to the stored template.

        Raises:
            StorageError: If file operation fails.
            TemplateError: If template exists and overwrite is False.
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise StorageError(f"Source file not found: {source_path}")

        if not source_path.suffix.lower() == ".docx":
            raise TemplateError("Template must be a .docx file")

        # Determine target name
        if name:
            name = sanitize_filename(name)
            if not name.endswith(".docx"):
                name = f"{name}.docx"
        else:
            name = source_path.name

        target_path = self._templates_dir / name

        if target_path.exists() and not overwrite:
            raise TemplateError(f"Template already exists: {name}")

        try:
            shutil.copy2(source_path, target_path)
            return target_path
        except OSError as e:
            raise StorageError(f"Failed to copy template: {e}") from e

    def remove_template(self, name: str) -> bool:
        """Remove a template from storage.

        Args:
            name: Template name (without .docx extension).

        Returns:
            True if template was removed.

        Raises:
            TemplateError: If template not found.
        """
        path = self.get_template_path(name)

        try:
            path.unlink()
            return True
        except OSError as e:
            raise StorageError(f"Failed to remove template: {e}") from e

    def get_template_info(self, name: str) -> dict:
        """Get information about a template.

        Args:
            name: Template name (without .docx extension).

        Returns:
            Dictionary with template information.

        Raises:
            TemplateError: If template not found.
        """
        path = self.get_template_path(name)
        stat = path.stat()

        return {
            "name": path.stem,
            "path": str(path),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "hash": get_file_hash(path),
        }
