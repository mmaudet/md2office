"""API request and response models."""

from __future__ import annotations

from typing import Any

import msgspec


class ConvertRequest(msgspec.Struct, frozen=True):
    """Request body for conversion endpoint."""

    markdown: str
    template: str | None = None
    variables: dict[str, Any] | None = None
    filename: str = "document.docx"


class ConvertResponse(msgspec.Struct, frozen=True):
    """Response for conversion endpoint (when returning JSON)."""

    success: bool
    filename: str
    size: int
    message: str | None = None


class TemplateInfo(msgspec.Struct, frozen=True):
    """Template information."""

    name: str
    size: int
    modified: float
    path: str | None = None


class TemplateListResponse(msgspec.Struct, frozen=True):
    """Response for template listing."""

    templates: list[TemplateInfo]
    count: int


class TemplateUploadResponse(msgspec.Struct, frozen=True):
    """Response for template upload."""

    success: bool
    name: str
    message: str | None = None


class ErrorResponse(msgspec.Struct, frozen=True):
    """Error response."""

    error: str
    details: dict[str, Any] | None = None


class HealthResponse(msgspec.Struct, frozen=True):
    """Health check response."""

    status: str
    version: str


class BatchConvertRequest(msgspec.Struct, frozen=True):
    """Request for batch conversion."""

    files: list[str]  # List of markdown content strings
    template: str | None = None
    variables: dict[str, Any] | None = None


class BatchConvertResponse(msgspec.Struct, frozen=True):
    """Response for batch conversion."""

    success: bool
    count: int
    message: str | None = None
