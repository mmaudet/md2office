"""Pytest configuration and fixtures for md2office tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown():
    """Sample Markdown content for testing."""
    return """# Test Document

This is a **bold** and *italic* test.

## Section 1

A paragraph with `inline code` and a [link](https://example.com).

### Subsection

- Item 1
- Item 2
- Item 3

1. First
2. Second
3. Third

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| A        | B        | C        |
| D        | E        | F        |

## Admonition

> [!NOTE]
> This is a note admonition.

> [!WARNING]
> This is a warning.

---

End of document.
"""


@pytest.fixture
def simple_markdown():
    """Simple Markdown content for basic testing."""
    return """# Hello World

This is a simple test document.

- Item one
- Item two
"""


@pytest.fixture
def template_variables():
    """Sample template variables."""
    return {
        "title": "Test Document",
        "author": "Test Author",
        "date": "2026-01-18",
    }
