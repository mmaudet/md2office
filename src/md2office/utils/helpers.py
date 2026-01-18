"""Helper utilities for md2office."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing/replacing invalid characters.

    Args:
        filename: Original filename.

    Returns:
        Sanitized filename safe for filesystem use.
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(". ")
    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"
    # Limit length (255 is common max for most filesystems)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized


def ensure_dir(path: Path | str) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path.

    Returns:
        Path object to the directory.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_hash(path: Path | str, algorithm: str = "sha256") -> str:
    """Calculate hash of a file.

    Args:
        path: Path to the file.
        algorithm: Hash algorithm (default: sha256).

    Returns:
        Hexadecimal hash string.
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: Suffix to append if truncated.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def normalize_line_endings(text: str) -> str:
    """Normalize line endings to Unix style (LF).

    Args:
        text: Text with potentially mixed line endings.

    Returns:
        Text with normalized line endings.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n")
