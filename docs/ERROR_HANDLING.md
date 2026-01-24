# Error Handling Guide

**Version 0.1.0**

This guide documents the exception hierarchy, error handling patterns, and best practices for md2office.

## Table of Contents

1. [Exception Hierarchy](#exception-hierarchy)
2. [Exception Types](#exception-types)
3. [When Exceptions Are Raised](#when-exceptions-are-raised)
4. [Catching and Handling Exceptions](#catching-and-handling-exceptions)
5. [API Error Response Format](#api-error-response-format)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

## Exception Hierarchy

All md2office exceptions inherit from a common base exception, allowing you to catch all library errors or specific types:

```
Exception (built-in)
└── Md2OfficeError (base exception)
    ├── ParserError (Markdown parsing errors)
    ├── BuilderError (DOCX building errors)
    ├── TemplateError (template operations errors)
    ├── ConfigError (configuration errors)
    ├── ValidationError (input validation errors)
    └── StorageError (file storage errors)
```

## Exception Types

All exceptions are defined in `src/md2office/core/exceptions.py`.

### Md2OfficeError

**Base exception for all md2office errors.**

```python
class Md2OfficeError(Exception):
    def __init__(self, message: str, details: dict | None = None) -> None:
        self.message = message
        self.details = details or {}
```

**Attributes:**
- `message` (str): Human-readable error message
- `details` (dict): Optional dictionary with additional error context

**Usage:** Catch this to handle all md2office errors uniformly.

### ParserError

**Raised during Markdown parsing operations.**

Inherits from `Md2OfficeError`. Indicates a problem parsing the input Markdown content.

### BuilderError

**Raised during DOCX document construction.**

Inherits from `Md2OfficeError`. Indicates a problem building the output DOCX file.

### TemplateError

**Raised for template-related operations.**

Inherits from `Md2OfficeError`. Indicates problems loading, rendering, or managing DOCX templates.

### ConfigError

**Raised for configuration errors.**

Inherits from `Md2OfficeError`. Indicates problems with configuration files or settings.

### ValidationError

**Raised for input validation failures.**

Inherits from `Md2OfficeError`. Indicates invalid input data or parameters.

### StorageError

**Raised for file storage operations.**

Inherits from `Md2OfficeError`. Indicates problems with file system operations.

## When Exceptions Are Raised

### ParserError

**Location:** `src/md2office/parser/markdown_parser.py`

| Line | Context | When Raised |
|------|---------|-------------|
| 70 | `parse()` method | Failed to parse Markdown content with mistune |
| 434 | `parse_file()` method | Cannot read Markdown file from disk |

**Common causes:**
- Malformed Markdown syntax (rare, mistune is forgiving)
- File reading errors (permissions, not found)
- Encoding issues

### BuilderError

**Location:** `src/md2office/builder/docx_builder.py`

| Line | Context | When Raised |
|------|---------|-------------|
| 155 | `build()` method | Failed to build DOCX document structure |

**Common causes:**
- Invalid document structure
- python-docx internal errors
- Style application failures

### TemplateError

**Location:** `src/md2office/template/storage.py` and `src/md2office/template/engine.py`

| File | Line | Context | When Raised |
|------|------|---------|-------------|
| storage.py | 72 | `get_template_path()` | Template file not found by name |
| storage.py | 115 | `add_template()` | Uploaded file is not a .docx file |
| storage.py | 128 | `add_template()` | Template already exists (overwrite=False) |
| engine.py | 61 | `_load_template()` | Failed to load DOCX template file |
| engine.py | 273 | `_render_text()` | Jinja2 template syntax error in variable |
| engine.py | 275 | `_render_text()` | Template rendering failed |

**Common causes:**
- Template file not found
- Invalid DOCX file structure
- Jinja2 syntax errors in `{{variables}}`
- Missing required variables
- Template already exists

### ConfigError

**Location:** `src/md2office/core/config.py`

| Line | Context | When Raised |
|------|---------|-------------|
| 108 | `load_config()` | Invalid YAML syntax in config file |
| 110 | `load_config()` | Cannot read config file |
| 154 | `validate()` | Config file not found at path |
| 168 | `validate()` | Invalid configuration structure |
| 197 | `load_styles_mapping()` | Invalid styles mapping YAML |

**Common causes:**
- YAML syntax errors
- Missing config files
- Invalid configuration values
- File permission issues

### ValidationError

**Location:** Currently not raised in codebase (reserved for future use)

**Intended use:** Input validation failures in API requests or CLI arguments.

### StorageError

**Location:** `src/md2office/template/storage.py`

| Line | Context | When Raised |
|------|---------|-------------|
| 112 | `add_template()` | Source template file not found |
| 134 | `add_template()` | Failed to copy template to storage |
| 154 | `remove_template()` | Failed to remove template file |

**Common causes:**
- File not found
- Insufficient permissions
- Disk space issues
- File system errors

## Catching and Handling Exceptions

### Python API Usage

#### Catch All md2office Errors

```python
from md2office import convert
from md2office.core.exceptions import Md2OfficeError

try:
    convert("document.md", "output.docx", template="corporate")
except Md2OfficeError as e:
    print(f"Conversion failed: {e.message}")
    if e.details:
        print(f"Details: {e.details}")
```

#### Catch Specific Exceptions

```python
from md2office import convert
from md2office.core.exceptions import TemplateError, ParserError

try:
    convert("document.md", "output.docx", template="custom-template")
except TemplateError as e:
    print(f"Template error: {e.message}")
    # Handle template issues (e.g., try default template)
    convert("document.md", "output.docx")
except ParserError as e:
    print(f"Markdown parsing error: {e.message}")
    # Handle parser issues
except Exception as e:
    print(f"Unexpected error: {e}")
```

#### Access Error Details

```python
from md2office.core.converter import Converter
from md2office.core.exceptions import BuilderError

try:
    converter = Converter(template_name="corporate")
    doc_bytes = converter.convert("# Hello\n\nThis is a test.")
except BuilderError as e:
    print(f"Build error: {e.message}")
    # Details might contain:
    # - Element that failed
    # - Style name that caused issue
    # - Line number in Markdown
    for key, value in e.details.items():
        print(f"  {key}: {value}")
```

### CLI Usage

The CLI automatically catches exceptions and displays user-friendly messages:

```bash
$ md2office convert document.md -t nonexistent
Error: Template error: Template not found: nonexistent

$ md2office convert invalid.md
Error: Markdown parsing error: Cannot read file: [Errno 2] No such file or directory: 'invalid.md'
```

### REST API Usage

API endpoints catch exceptions and return structured error responses. See [API Error Response Format](#api-error-response-format) below.

## API Error Response Format

All md2office API endpoints return consistent error responses when exceptions occur.

### Error Response Structure

**Model:** `ErrorResponse` (`src/md2office/api/models.py:52-56`)

```python
class ErrorResponse(msgspec.Struct, frozen=True):
    """Error response."""
    error: str
    details: dict[str, Any] | None = None
```

### HTTP Status Codes

| Exception Type | HTTP Status | Description |
|----------------|-------------|-------------|
| `Md2OfficeError` (all types) | 400 Bad Request | Client error (invalid input, template not found, etc.) |
| Other exceptions | 400 Bad Request | Catch-all for unexpected errors |

### Example Error Responses

#### Template Not Found

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Test",
    "template": "nonexistent"
  }'
```

**Response:**
```json
{
  "error": "Template not found: nonexistent",
  "details": {}
}
```

**Status:** 400 Bad Request

#### Template Syntax Error

**Request:**
```bash
curl -X POST http://localhost:8080/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Test",
    "template": "corporate",
    "variables": {"title": "My Doc"}
  }'
```

If the template contains invalid Jinja2 syntax like `{{unclosed`:

**Response:**
```json
{
  "error": "Template syntax error: unexpected 'end of template'",
  "details": {}
}
```

**Status:** 400 Bad Request

#### Parsing Error

If Markdown file cannot be read:

**Response:**
```json
{
  "error": "Failed to parse Markdown: invalid content",
  "details": {}
}
```

**Status:** 400 Bad Request

### API Error Handling Pattern

**Location:** `src/md2office/api/routes.py`

All API endpoints follow this pattern:

```python
@post()
async def convert_markdown(self, data: ConvertRequest) -> Response[bytes]:
    try:
        converter = Converter(
            template_name=data.template,
            variables=data.variables,
        )
        doc_bytes = converter.convert(data.markdown)
        return Response(content=doc_bytes, status_code=HTTP_200_OK)

    except Md2OfficeError as e:
        return Response(
            content=ErrorResponse(error=e.message, details=e.details),
            status_code=HTTP_400_BAD_REQUEST,
        )
```

## Best Practices

### 1. Catch Specific Exceptions When Possible

```python
# Good: Catch specific exceptions for targeted handling
try:
    result = converter.convert(markdown)
except TemplateError:
    # Try with default template
    result = converter.convert(markdown, template=None)
except ParserError:
    # Log parsing issue, maybe clean the input
    markdown = clean_markdown(markdown)
    result = converter.convert(markdown)

# Avoid: Catching too broadly
try:
    result = converter.convert(markdown)
except Exception:
    # Lost context about what went wrong
    pass
```

### 2. Use Error Details for Debugging

```python
try:
    converter = Converter(template_name="corporate")
    doc_bytes = converter.convert(markdown)
except Md2OfficeError as e:
    logger.error(f"Conversion failed: {e.message}")
    # Log details for debugging
    logger.debug(f"Error details: {e.details}")
    # Re-raise or handle appropriately
    raise
```

### 3. Provide User-Friendly Messages

```python
from md2office.core.exceptions import TemplateError

try:
    convert(input_file, output_file, template=template_name)
except TemplateError as e:
    if "not found" in e.message:
        print(f"Template '{template_name}' doesn't exist.")
        print(f"Available templates: {list_templates()}")
    else:
        print(f"Template error: {e.message}")
except Md2OfficeError as e:
    print(f"Conversion error: {e.message}")
```

### 4. Chain Exceptions for Context

When raising md2office exceptions, use `from` to preserve the original traceback:

```python
try:
    # Some operation
    result = risky_operation()
except ValueError as e:
    raise TemplateError(f"Invalid template: {e}") from e
```

This is already done throughout the codebase. For example:
- `src/md2office/parser/markdown_parser.py:70`
- `src/md2office/template/engine.py:61`
- `src/md2office/builder/docx_builder.py:155`

### 5. Add Details for Complex Errors

```python
from md2office.core.exceptions import BuilderError

def apply_style(element, style_name):
    try:
        element.style = style_name
    except KeyError as e:
        raise BuilderError(
            f"Style not found: {style_name}",
            details={
                "style": style_name,
                "element": element.__class__.__name__,
                "available_styles": list(document.styles.keys())
            }
        ) from e
```

### 6. Handle File Operations Gracefully

```python
from pathlib import Path
from md2office import convert
from md2office.core.exceptions import ParserError, StorageError

input_file = Path("document.md")
output_file = Path("output.docx")

try:
    # Check file exists before conversion
    if not input_file.exists():
        print(f"Input file not found: {input_file}")
        return

    convert(str(input_file), str(output_file))
    print(f"Success! Created {output_file}")

except ParserError as e:
    print(f"Could not parse {input_file}: {e.message}")
except StorageError as e:
    print(f"File operation failed: {e.message}")
except Md2OfficeError as e:
    print(f"Conversion failed: {e.message}")
```

### 7. Test Error Conditions

Write tests for error scenarios:

```python
import pytest
from md2office.core.exceptions import TemplateError
from md2office.template.storage import TemplateStorage

def test_template_not_found():
    storage = TemplateStorage()

    with pytest.raises(TemplateError, match="Template not found"):
        storage.get_template_path("nonexistent")

def test_invalid_template_format():
    storage = TemplateStorage()

    with pytest.raises(TemplateError, match="must be a .docx file"):
        storage.add_template(Path("template.txt"))
```

## Examples

### Example 1: CLI with Error Recovery

```python
from pathlib import Path
from md2office import convert
from md2office.core.exceptions import TemplateError, Md2OfficeError

def convert_with_fallback(input_path: str, template: str = "corporate"):
    """Convert with fallback to default template on error."""
    output_path = Path(input_path).with_suffix(".docx")

    try:
        # Try with specified template
        convert(input_path, str(output_path), template=template)
        print(f"✓ Converted with '{template}' template")
        return output_path

    except TemplateError as e:
        print(f"⚠ Template error: {e.message}")
        print(f"  Trying default template...")

        try:
            # Fallback to default (no template)
            convert(input_path, str(output_path))
            print(f"✓ Converted with default template")
            return output_path
        except Md2OfficeError as e:
            print(f"✗ Conversion failed: {e.message}")
            raise

    except Md2OfficeError as e:
        print(f"✗ Conversion failed: {e.message}")
        raise
```

### Example 2: Batch Processing with Error Logging

```python
from pathlib import Path
from md2office import convert
from md2office.core.exceptions import Md2OfficeError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_convert(input_dir: Path, output_dir: Path, template: str = None):
    """Convert all Markdown files in a directory."""
    output_dir.mkdir(exist_ok=True)

    markdown_files = list(input_dir.glob("*.md"))
    results = {"success": [], "failed": []}

    for md_file in markdown_files:
        output_file = output_dir / md_file.with_suffix(".docx").name

        try:
            convert(str(md_file), str(output_file), template=template)
            results["success"].append(md_file.name)
            logger.info(f"✓ Converted: {md_file.name}")

        except Md2OfficeError as e:
            results["failed"].append({
                "file": md_file.name,
                "error": e.message,
                "details": e.details
            })
            logger.error(f"✗ Failed: {md_file.name} - {e.message}")

    # Summary
    logger.info(f"\nResults: {len(results['success'])} succeeded, {len(results['failed'])} failed")

    if results["failed"]:
        logger.info("\nFailed files:")
        for failure in results["failed"]:
            logger.info(f"  - {failure['file']}: {failure['error']}")

    return results
```

### Example 3: API Client with Retry Logic

```python
import httpx
from typing import Optional
import time

class Md2OfficeClient:
    """Client for md2office REST API with error handling."""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.Client()

    def convert(
        self,
        markdown: str,
        template: Optional[str] = None,
        variables: Optional[dict] = None,
        max_retries: int = 3
    ) -> bytes:
        """Convert Markdown to DOCX via API.

        Returns:
            DOCX file bytes

        Raises:
            httpx.HTTPStatusError: On HTTP errors
        """
        url = f"{self.base_url}/api/v1/convert"
        payload = {
            "markdown": markdown,
            "template": template,
            "variables": variables,
            "filename": "document.docx"
        }

        for attempt in range(max_retries):
            try:
                response = self.client.post(url, json=payload)
                response.raise_for_status()
                return response.content

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:
                    # Client error - don't retry
                    error_data = e.response.json()
                    raise ValueError(
                        f"Conversion error: {error_data.get('error')}"
                    ) from e

                elif attempt < max_retries - 1:
                    # Server error - retry with backoff
                    wait = 2 ** attempt
                    print(f"Retry {attempt + 1}/{max_retries} in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"Connection error, retry in {wait}s...")
                    time.sleep(wait)
                else:
                    raise

# Usage
client = Md2OfficeClient()

try:
    docx_bytes = client.convert(
        markdown="# My Document\n\nContent here.",
        template="corporate",
        variables={"author": "John Doe"}
    )
    with open("output.docx", "wb") as f:
        f.write(docx_bytes)
    print("✓ Conversion successful")

except ValueError as e:
    print(f"✗ Conversion failed: {e}")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
```

### Example 4: Template Management with Error Handling

```python
from pathlib import Path
from md2office.template.storage import TemplateStorage
from md2office.core.exceptions import TemplateError, StorageError

def upload_template_safe(template_path: Path, name: str = None) -> bool:
    """Upload a template with comprehensive error handling.

    Returns:
        True if successful, False otherwise
    """
    storage = TemplateStorage()
    template_name = name or template_path.stem

    try:
        # Validate file exists
        if not template_path.exists():
            print(f"✗ File not found: {template_path}")
            return False

        # Validate file extension
        if template_path.suffix != ".docx":
            print(f"✗ Invalid file type: {template_path.suffix}")
            print(f"  Templates must be .docx files")
            return False

        # Try to upload
        result_path = storage.add_template(
            template_path,
            name=template_name,
            overwrite=False
        )
        print(f"✓ Template uploaded: {result_path.stem}")
        return True

    except TemplateError as e:
        if "already exists" in e.message:
            print(f"⚠ Template '{template_name}' already exists")

            # Ask user if they want to overwrite
            response = input("  Overwrite? (y/N): ").strip().lower()
            if response == 'y':
                try:
                    result_path = storage.add_template(
                        template_path,
                        name=template_name,
                        overwrite=True
                    )
                    print(f"✓ Template updated: {result_path.stem}")
                    return True
                except Exception as e:
                    print(f"✗ Failed to overwrite: {e}")
                    return False
            else:
                return False
        else:
            print(f"✗ Template error: {e.message}")
            return False

    except StorageError as e:
        print(f"✗ Storage error: {e.message}")
        if e.details:
            print(f"  Details: {e.details}")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
```

---

**Related Documentation:**
- [User Guide](README.md)
- [API Documentation](API.md)
- [Template Guide](TEMPLATES.md)
- [Source: src/md2office/core/exceptions.py](../src/md2office/core/exceptions.py)
