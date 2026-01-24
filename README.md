# md2office

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-34%20passed-success.svg)](tests/)

**Convert Markdown to professional Microsoft Word (DOCX) documents with corporate template support.**

md2office is a Python-based open source tool that transforms Markdown files into polished Word documents, complete with style mapping, template injection, and support for advanced features like admonitions, tables with merged cells, and clickable hyperlinks.

---

## Features

- **Full Markdown Support** - Headings, lists, tables, code blocks, blockquotes, links, and more
- **Corporate Templates** - Use custom DOCX templates with predefined styles
- **Style Mapping** - Automatic mapping of Markdown elements to Word styles
- **Cross-Template Compatibility** - Works with different template style naming conventions
- **Variable Injection** - Jinja2-style `{{variable}}` substitution in documents
- **GitHub Admonitions** - Support for `[!NOTE]`, `[!WARNING]`, `[!TIP]`, `[!IMPORTANT]`, `[!CAUTION]`
- **Advanced Tables** - Headers, alternating rows, merged cells (rowspan/colspan)
- **Clickable Hyperlinks** - Real Word hyperlinks, not just styled text
- **REST API** - HTTP API for integration into workflows
- **CLI** - Command-line interface for scripting and automation
- **Docker Ready** - Containerized deployment option

## Installation

### Using uv (recommended)

```bash
# Clone the repository
git clone https://github.com/mmaudet/md2office.git
cd md2office

# Install dependencies
uv sync

# Verify installation
uv run md2office --help
```

### Using pip

```bash
pip install md2office
```

## Quick Start

### Command Line

```bash
# Basic conversion
md2office convert document.md

# With a specific template
md2office convert document.md -t professional -o output.docx

# With variable injection
md2office convert proposal.md -t linagora -o proposal.docx \
  -v title="Technical Proposal" \
  -v author="John Doe" \
  -v date="2026-01-18"
```

### Python API

```python
from md2office import convert

# Simple conversion
convert("input.md", "output.docx")

# With template and variables
convert(
    "proposal.md",
    "proposal.docx",
    template="professional",
    variables={
        "title": "Technical Proposal",
        "author": "John Doe",
        "date": "2026-01-18"
    }
)
```

### REST API

```bash
# Start the server
md2office serve --port 8080

# Convert a file
curl -X POST http://localhost:8080/api/v1/convert \
  -F "file=@document.md" \
  -F "template=professional" \
  -o output.docx
```

### Docker Deployment

```bash
# Quick start with docker-compose
docker-compose up -d

# API is now available at http://localhost:8080
curl -X POST http://localhost:8080/api/v1/convert \
  -F "file=@document.md" \
  -F "template=professional" \
  -o output.docx
```

**Environment Variables Quick Reference:**

| Variable | Default | Description |
|----------|---------|-------------|
| `API_PORT` | `8080` | API server port |
| `API_HOST` | `0.0.0.0` | API server host |
| `TEMPLATE_DIR` | `/app/templates` | Custom templates directory |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `MAX_FILE_SIZE` | `10485760` | Max upload size in bytes (10MB default) |

For detailed deployment instructions, volume mounting, production setup, and troubleshooting, see the [Docker Deployment Guide](docs/DOCKER.md).

## Supported Markdown Features

| Feature | Syntax | Notes |
|---------|--------|-------|
| Headings | `# H1` to `###### H6` | Maps to Word Heading styles |
| Bold | `**text**` | Strong emphasis |
| Italic | `*text*` | Emphasis |
| Code inline | `` `code` `` | Monospace font |
| Strikethrough | `~~text~~` | Strikethrough formatting |
| Links | `[text](url)` | Clickable hyperlinks |
| Bullet lists | `- item` | Nested supported |
| Numbered lists | `1. item` | Nested supported |
| Code blocks | ` ```language ` | Left-aligned, monospace |
| Tables | `\| A \| B \|` | Headers, merged cells |
| Blockquotes | `> quote` | Indented with border |
| Admonitions | `> [!NOTE]` | Styled callout boxes |
| Horizontal rules | `---` | Section separator |

## Templates

md2office includes two built-in templates:

| Template | Description |
|----------|-------------|
| `professional` | Clean business template with blue accents |
| `linagora` | LINAGORA corporate template with red branding |

### Using Templates

```bash
# List available templates
md2office templates

# Use a specific template
md2office convert doc.md -t professional

# Add a custom template
md2office template-add my-company.docx --name corporate
```

### Creating Custom Templates

1. Create a DOCX document in Word/LibreOffice
2. Define styles: `Heading 1-6`, `Normal`, `Code`, `Quote`, etc.
3. Add headers/footers with `{{variable}}` placeholders
4. Save and add to md2office:

```bash
md2office template-add my-template.docx --name custom
```

## Variable Injection

md2office supports Jinja2-style variable injection in both Markdown content and DOCX templates.

### In Markdown Content

```markdown
# Report for {{customer}}

Prepared by {{author}} on {{date}}.

Project: {{project}}
```

### In Templates (Headers/Footers)

Variables can be placed in template headers, footers, and cover pages:

```
Header: {{title}} | {{date}}
Footer: {{author}} - Page X of Y
```

### Usage

```bash
# CLI
md2office convert report.md -o report.docx \
  -v customer="Acme Corp" \
  -v author="Jane Smith" \
  -v date="January 2026" \
  -v project="Q1 Analysis"

# Python API
convert(
    "report.md",
    "report.docx",
    variables={
        "customer": "Acme Corp",
        "author": "Jane Smith",
        "date": "January 2026"
    }
)
```

### LINAGORA Template Variables

| Variable | Location | Description |
|----------|----------|-------------|
| `{{title}}` | Header | Document title |
| `{{subtitle}}` | Header | Document subtitle |
| `{{author}}` | Footer | Author name |
| `{{date}}` | Header/Footer | Document date |
| `{{customer}}` | Body | Customer name |
| `{{project}}` | Body | Project name |
| `{{version}}` | Footer | Document version |
| `{{classification}}` | Footer | Confidentiality level |

## Configuration

### Style Mapping

Configure Markdown-to-Word style mappings in `config/styles-mapping.yaml`:

```yaml
headings:
  h1: "Heading 1"
  h2: "Heading 2"
  h3: "Heading 3"

paragraph:
  normal: "Text body"
  quote: "Quote"

code:
  inline: "Code in line"
  block: "Code"

table:
  header_bg: "c00d2d"    # Header background color
  header_text: "FFFFFF"  # Header text color
  alternating_rows: true
```

### Cross-Template Compatibility

md2office automatically handles different style naming conventions across templates:

| Configuration | Template A | Template B |
|---------------|-----------|-----------|
| `code.block: "Code"` | Uses "Code" | Falls back to "Code Block" |
| `paragraph.normal: "Text body"` | Uses "Text body" | Falls back to "Body Text" |

## Development

```bash
# Clone and setup
git clone https://github.com/mmaudet/md2office.git
cd md2office
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=md2office --cov-report=html

# Lint and format
uv run ruff check .
uv run ruff format .

# Start development server
md2office serve --reload
```

## Project Structure

```
md2office/
├── src/md2office/
│   ├── api/           # REST API routes and models
│   ├── builder/       # DOCX document construction
│   ├── core/          # Configuration, converter, exceptions
│   ├── parser/        # Markdown parsing (mistune-based)
│   ├── template/      # Template engine and storage
│   └── utils/         # Helper functions
├── config/            # Style mappings and configuration
├── templates/         # DOCX templates
├── tests/             # Test suite
└── docs/              # Documentation
```

## Documentation

- [User Guide (English)](docs/README.md) - Complete usage documentation
- [Guide Utilisateur (Français)](docs/README.fr.md) - Documentation complète en français
- [API Reference](docs/README.md#rest-api) - REST API endpoints
- [Template Guide](docs/README.md#creating-custom-templates) - Creating custom templates
- [Error Handling Guide](docs/ERROR_HANDLING.md) - Error handling and exception reference

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:

- Reporting bugs
- Suggesting features
- Submitting pull requests
- Code style guidelines

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [python-docx](https://python-docx.readthedocs.io/) - Word document generation
- [mistune](https://github.com/lepture/mistune) - Markdown parsing
- [Litestar](https://litestar.dev/) - REST API framework

---

Made with care by the md2office contributors.
