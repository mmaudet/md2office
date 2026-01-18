"""Custom exceptions for md2office."""

from __future__ import annotations


class Md2OfficeError(Exception):
    """Base exception for all md2office errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ParserError(Md2OfficeError):
    """Error during Markdown parsing."""

    pass


class BuilderError(Md2OfficeError):
    """Error during DOCX building."""

    pass


class TemplateError(Md2OfficeError):
    """Error related to template operations."""

    pass


class ConfigError(Md2OfficeError):
    """Error in configuration."""

    pass


class ValidationError(Md2OfficeError):
    """Error in input validation."""

    pass


class StorageError(Md2OfficeError):
    """Error in file storage operations."""

    pass
