# md2office

Convert Markdown to professional DOCX documents with corporate template support.

## Features

- **Markdown to DOCX conversion** with full formatting support
- **Corporate templates** with style mapping
- **Variable injection** using Jinja2 syntax (`{{variable}}`)
- **Admonitions** support (NOTE, WARNING, TIP, etc.)
- **Tables** with full formatting (borders, headers, alternating rows)
- **REST API** for integration
- **CLI** for command-line usage
- **Docker** support for easy deployment

## Installation

```bash
# Using uv (recommended)
uv sync
uv run md2office --help

# Or using pip
pip install md2office
```

## Quick Start

### CLI Usage

```bash
# Basic conversion
md2office convert input.md -o output.docx

# With template
md2office convert input.md --template corporate -o output.docx

# With variables
md2office convert input.md -o output.docx --var author="John Doe" --var date="2026-01-18"
```

### API Usage

```bash
# Start the server
uvicorn md2office.main:app --host 0.0.0.0 --port 8080

# Convert a file
curl -X POST http://localhost:8080/api/v1/convert \
  -F "file=@input.md" \
  -F "template=default" \
  -o output.docx
```

### Python API

```python
from md2office import convert

# Simple conversion
convert("input.md", "output.docx")

# With options
convert(
    "input.md",
    "output.docx",
    template="corporate",
    variables={"author": "John Doe", "date": "2026-01-18"}
)
```

## Supported Markdown Features

- Headings (H1-H6)
- Paragraphs with inline formatting (bold, italic, code, links)
- Ordered and unordered lists (nested)
- Code blocks with syntax highlighting
- Tables with headers
- Blockquotes
- Admonitions (`> [!NOTE]`, `> [!WARNING]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!CAUTION]`)
- Images
- Horizontal rules

## Configuration

### Style Mapping

Configure how Markdown elements map to Word styles in `config/styles-mapping.yaml`:

```yaml
headings:
  h1: "Heading 1"
  h2: "Heading 2"
  h3: "Heading 3"

paragraph:
  normal: "Normal"

code:
  inline: "Code Char"
  block: "Code Block"
```

### Templates

Place your DOCX templates in the `templates/` directory. Templates can include:

- Predefined styles
- Headers and footers with variables
- Cover pages
- Custom formatting

## Development

```bash
# Clone the repository
git clone https://github.com/mmaudet/md2office.git
cd md2office

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format .

# Run the development server
uv run litestar run --reload
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
