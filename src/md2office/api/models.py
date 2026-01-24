"""API request and response models."""

from __future__ import annotations

from typing import Any

import msgspec


class ConvertRequest(msgspec.Struct, frozen=True):
    """Request body for conversion endpoint.

    Attributes:
        markdown: The Markdown content to convert to DOCX format.
            Example: "# Title\\n\\nParagraph with **bold** text"
        template: Optional template name to use for styling.
            Example: "corporate" or "minimal". If None, uses default template.
        variables: Optional dictionary of template variables for substitution.
            Example: {"author": "John Doe", "date": "2024-01-15"}
        filename: Output filename for the generated DOCX file.
            Default: "document.docx"
            Example: "report.docx"

    Example:
        ```json
        {
            "markdown": "# Report\\n\\nThis is a test report.",
            "template": "corporate",
            "variables": {"author": "Jane Smith"},
            "filename": "monthly-report.docx"
        }
        ```
    """

    markdown: str
    template: str | None = None
    variables: dict[str, Any] | None = None
    filename: str = "document.docx"


class ConvertResponse(msgspec.Struct, frozen=True):
    """Response for conversion endpoint (when returning JSON).

    Attributes:
        success: Whether the conversion was successful.
            Example: true
        filename: The name of the generated DOCX file.
            Example: "document.docx"
        size: File size in bytes of the generated DOCX.
            Example: 15234
        message: Optional status or error message.
            Example: "Conversion completed successfully"

    Example:
        ```json
        {
            "success": true,
            "filename": "report.docx",
            "size": 15234,
            "message": "Conversion completed successfully"
        }
        ```
    """

    success: bool
    filename: str
    size: int
    message: str | None = None


class TemplateInfo(msgspec.Struct, frozen=True):
    """Template information for a DOCX template file.

    Attributes:
        name: Template filename without path.
            Example: "corporate.docx"
        size: Template file size in bytes.
            Example: 45678
        modified: Last modification timestamp (Unix epoch).
            Example: 1674123456.789
        path: Optional full file path to the template.
            Example: "/app/templates/corporate.docx"

    Example:
        ```json
        {
            "name": "corporate.docx",
            "size": 45678,
            "modified": 1674123456.789,
            "path": "/app/templates/corporate.docx"
        }
        ```
    """

    name: str
    size: int
    modified: float
    path: str | None = None


class TemplateListResponse(msgspec.Struct, frozen=True):
    """Response for template listing endpoint.

    Attributes:
        templates: List of available template information objects.
        count: Total number of templates available.
            Example: 3

    Example:
        ```json
        {
            "templates": [
                {"name": "corporate.docx", "size": 45678, "modified": 1674123456.789},
                {"name": "minimal.docx", "size": 12345, "modified": 1674123456.789}
            ],
            "count": 2
        }
        ```
    """

    templates: list[TemplateInfo]
    count: int


class TemplateUploadResponse(msgspec.Struct, frozen=True):
    """Response for template upload endpoint.

    Attributes:
        success: Whether the template upload was successful.
            Example: true
        name: The name of the uploaded template file.
            Example: "custom-template.docx"
        message: Optional status or error message about the upload.
            Example: "Template uploaded successfully"

    Example:
        ```json
        {
            "success": true,
            "name": "custom-template.docx",
            "message": "Template uploaded successfully"
        }
        ```
    """

    success: bool
    name: str
    message: str | None = None


class ErrorResponse(msgspec.Struct, frozen=True):
    """Error response for failed API requests.

    Attributes:
        error: Human-readable error message describing what went wrong.
            Example: "Invalid markdown syntax"
        details: Optional dictionary with additional error context.
            Example: {"line": 42, "column": 15, "code": "PARSE_ERROR"}

    Example:
        ```json
        {
            "error": "Template not found",
            "details": {
                "template_name": "nonexistent.docx",
                "available_templates": ["corporate.docx", "minimal.docx"]
            }
        }
        ```
    """

    error: str
    details: dict[str, Any] | None = None


class HealthResponse(msgspec.Struct, frozen=True):
    """Health check response for API status monitoring.

    Attributes:
        status: Current health status of the API service.
            Example: "healthy" or "degraded"
        version: API version string.
            Example: "0.1.0"

    Example:
        ```json
        {
            "status": "healthy",
            "version": "0.1.0"
        }
        ```
    """

    status: str
    version: str


class BatchConvertRequest(msgspec.Struct, frozen=True):
    """Request for batch conversion of multiple markdown files.

    Attributes:
        files: List of markdown content strings to convert.
            Example: ["# Doc 1\\n\\nContent", "# Doc 2\\n\\nMore content"]
        template: Optional template name to use for all conversions.
            Example: "corporate". If None, uses default template.
        variables: Optional dictionary of template variables for all files.
            Example: {"company": "ACME Corp", "year": "2024"}

    Example:
        ```json
        {
            "files": [
                "# Report 1\\n\\nFirst document",
                "# Report 2\\n\\nSecond document"
            ],
            "template": "corporate",
            "variables": {"author": "Team Lead"}
        }
        ```
    """

    files: list[str]
    template: str | None = None
    variables: dict[str, Any] | None = None


class BatchConvertResponse(msgspec.Struct, frozen=True):
    """Response for batch conversion endpoint.

    Attributes:
        success: Whether the batch conversion was successful.
            Example: true
        count: Number of files successfully converted.
            Example: 5
        message: Optional status or error message about the batch operation.
            Example: "Successfully converted 5 files"

    Example:
        ```json
        {
            "success": true,
            "count": 5,
            "message": "Successfully converted 5 files"
        }
        ```
    """

    success: bool
    count: int
    message: str | None = None
