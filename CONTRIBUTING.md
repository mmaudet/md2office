# Contributing to md2office

Thank you for your interest in contributing to md2office! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/md2office.git
   cd md2office
   ```

3. **Install dependencies**:
   ```bash
   uv sync
   ```

4. **Verify the setup**:
   ```bash
   uv run pytest
   uv run md2office --help
   ```

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

When reporting a bug, include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, md2office version)
- **Sample Markdown file** that triggers the issue (if applicable)
- **Generated DOCX file** or error messages

### Suggesting Features

Feature requests are welcome! Please include:

- **Use case** - Why is this feature needed?
- **Proposed solution** - How should it work?
- **Alternatives considered** - Other approaches you've thought about
- **Additional context** - Screenshots, mockups, examples

### Submitting Pull Requests

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-description
   ```

2. **Make your changes** following the code style guidelines

3. **Write/update tests** for your changes

4. **Run the test suite**:
   ```bash
   uv run pytest
   ```

5. **Run linting**:
   ```bash
   uv run ruff check .
   uv run ruff format .
   ```

6. **Commit your changes**:
   ```bash
   git commit -m "Brief description of changes"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request** on GitHub

## Pull Request Process

1. **Title**: Use a clear, descriptive title
2. **Description**: Explain what changes you made and why
3. **Link issues**: Reference any related issues with `Fixes #123`
4. **Tests**: Ensure all tests pass
5. **Documentation**: Update docs if needed
6. **Review**: Wait for maintainer review and address feedback

### PR Checklist

- [ ] Tests pass locally (`uv run pytest`)
- [ ] Code is formatted (`uv run ruff format .`)
- [ ] No linting errors (`uv run ruff check .`)
- [ ] Documentation updated (if applicable)
- [ ] Commit messages are clear and descriptive

## Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

### Key Guidelines

- **Line length**: 100 characters maximum
- **Imports**: Sorted automatically by ruff
- **Docstrings**: Google style for all public functions/classes
- **Type hints**: Required for function signatures

### Example

```python
def convert_markdown(
    content: str,
    template: str | None = None,
    variables: dict[str, str] | None = None,
) -> bytes:
    """Convert Markdown content to DOCX bytes.

    Args:
        content: Markdown source text.
        template: Optional template name to use.
        variables: Optional variables for template injection.

    Returns:
        DOCX document as bytes.

    Raises:
        ConversionError: If conversion fails.
    """
    ...
```

### Running Linters

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_parser/test_markdown_parser.py

# Run with coverage
uv run pytest --cov=md2office --cov-report=html
```

### Writing Tests

- Place tests in the `tests/` directory
- Mirror the source structure (`src/md2office/parser/` → `tests/test_parser/`)
- Use descriptive test names: `test_parse_heading_level_one`
- Use pytest fixtures from `conftest.py`

### Test Example

```python
import pytest
from md2office.parser.markdown_parser import MarkdownParser


class TestMarkdownParser:
    """Tests for MarkdownParser."""

    def test_parse_heading_level_one(self):
        """Test parsing H1 headings."""
        parser = MarkdownParser()
        result = parser.parse("# Hello World")

        assert len(result) == 1
        assert result[0].level == 1
        assert result[0].text == "Hello World"
```

## Documentation

### Updating Documentation

- User documentation is in `docs/documentation.md`
- API documentation is generated from docstrings
- README.md provides a quick overview

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep examples up-to-date with the code
- Use proper Markdown formatting

## Project Structure

```
md2office/
├── src/md2office/
│   ├── api/           # REST API (Litestar)
│   ├── builder/       # DOCX construction
│   ├── core/          # Core logic and config
│   ├── parser/        # Markdown parsing
│   ├── template/      # Template engine
│   └── utils/         # Utilities
├── tests/             # Test suite
├── config/            # Configuration files
├── templates/         # DOCX templates
└── docs/              # Documentation
```

## Questions?

If you have questions, feel free to:

- Open a [GitHub Discussion](https://github.com/mmaudet/md2office/discussions)
- Create an [Issue](https://github.com/mmaudet/md2office/issues)

Thank you for contributing!
