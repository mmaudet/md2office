# md2office - User Guide

**Version 0.1.0**

md2office is an open source tool for converting Markdown files to professional Word (DOCX) documents with corporate template support and style mapping.

*[Version française disponible](README.fr.md)*

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Docker Deployment](#docker-deployment)
4. [Supported Markdown Features](#supported-markdown-features)
5. [Available Templates](#available-templates)
6. [Style Mapping](#style-mapping)
7. [Cross-Template Compatibility](#cross-template-compatibility)
8. [Template Variables](#template-variables)
9. [REST API](#rest-api)
10. [Advanced Configuration](#advanced-configuration)
11. [Troubleshooting](#troubleshooting)
12. [Support](#support)

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

# With specific template
md2office convert document.md -t professional -o output.docx

# With LINAGORA template and variables
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

# With options
convert(
    "proposal.md",
    "proposal.docx",
    template="linagora",
    variables={
        "title": "Technical Proposal",
        "author": "John Doe",
        "date": "2026-01-18"
    }
)
```

## Docker Deployment

md2office can be deployed as a containerized service using Docker and Docker Compose, providing an isolated and reproducible environment for conversions.

For comprehensive Docker deployment instructions, including production configurations, environment variables, and troubleshooting, see the **[Docker Deployment Guide](DOCKER.md)**.

### Quick Start with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  md2office:
    image: md2office:latest
    ports:
      - "8080:8080"
    environment:
      - MD2OFFICE_HOST=0.0.0.0
      - MD2OFFICE_PORT=8080
      - MD2OFFICE_LOG_LEVEL=info
    volumes:
      - ./templates:/app/templates
      - ./output:/app/output
```

Then start the service:

```bash
docker-compose up -d
```

The API will be available at `http://localhost:8080`.

## Supported Markdown Features

md2office supports a wide range of Markdown syntax, enabling the creation of rich, professional documents.

### Headings

Heading levels 1-6 are supported and map to Word `Heading 1` through `Heading 6` styles.

```markdown
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6
```

### Text Formatting

| Markdown | Result | Description |
|----------|--------|-------------|
| `**text**` | **bold** | Bold text |
| `*text*` | *italic* | Italic text |
| `***text***` | ***bold italic*** | Bold and italic |
| `` `code` `` | `inline code` | Monospace font (Liberation Mono) |
| `~~text~~` | ~~strikethrough~~ | Strikethrough text |
| `[link](url)` | [clickable link](https://example.com) | Clickable hyperlink |

### Lists

#### Bullet Lists

```markdown
- First item
- Second item
  - Sub-item
  - Another sub-item
- Third item
```

Result:
- First item
- Second item
  - Sub-item
  - Another sub-item
- Third item

#### Numbered Lists

```markdown
1. First step
2. Second step
   1. Sub-step A
   2. Sub-step B
3. Third step
```

Result:
1. First step
2. Second step
   1. Sub-step A
   2. Sub-step B
3. Third step

### Code Blocks

Code blocks are rendered with:
- Monospace font (Liberation Mono, 9pt)
- Forced left alignment
- Each line in a separate paragraph for optimal rendering

```python
def hello_world():
    """Demo function."""
    print("Hello, World!")
    return True
```

The language specified after the triple backticks is preserved for reference but does not enable syntax highlighting in DOCX.

### Tables

Markdown tables are converted to Word tables with:
- Colored headers (configurable)
- Alternating row colors (optional)
- Vertical centering of content
- Clickable hyperlink support

```markdown
| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

| Column A | Column B | Column C |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

#### Merged Cells

md2office supports cell merging with extended syntax:

- **Vertical merge (rowspan)**: Use `^^` to merge a cell with the one above
- **Horizontal merge (colspan)**: Use `>>` to merge a cell with the one to the left

**Vertical merge example:**

```markdown
| Category  | Product   | Price |
|-----------|-----------|-------|
| Fruits    | Apple     | $1.50 |
| ^^        | Orange    | $2.00 |
| ^^        | Banana    | $1.20 |
| Vegetables| Carrot    | $0.80 |
| ^^        | Tomato    | $1.50 |
```

| Category  | Product   | Price |
|-----------|-----------|-------|
| Fruits    | Apple     | $1.50 |
| ^^        | Orange    | $2.00 |
| ^^        | Banana    | $1.20 |
| Vegetables| Carrot    | $0.80 |
| ^^        | Tomato    | $1.50 |

**Horizontal merge example:**

```markdown
| Name      | Contact   | >>        |
|-----------|-----------|-----------|
| Smith     | Email     | Phone     |
| Johnson   | email@ex  | 01234567  |
```

| Name      | Contact   | >>        |
|-----------|-----------|-----------|
| Smith     | Email     | Phone     |
| Johnson   | email@ex  | 01234567  |

### Blockquotes

Blockquotes use the `Quote` style with a left border and italic formatting.

> This is a blockquote. It can contain **formatting** and span multiple lines for longer passages.

```markdown
> This is a blockquote. It can contain **formatting**
> and span multiple lines.
```

### Admonitions (GitHub-style)

md2office supports GitHub-style admonitions, rendered as colored tables with icons and vertical centering.

> [!NOTE]
> **Tag:** `> [!NOTE]` - Use notes for additional information helpful to the reader.

> [!TIP]
> **Tag:** `> [!TIP]` - Tips help users improve productivity or discover features.

> [!IMPORTANT]
> **Tag:** `> [!IMPORTANT]` - Highlight crucial information the reader shouldn't miss.

> [!WARNING]
> **Tag:** `> [!WARNING]` - Warn about potential risks or irreversible actions.

> [!CAUTION]
> **Tag:** `> [!CAUTION]` - Signal dangers or actions that could cause problems.

**Markdown syntax:**

```markdown
> [!NOTE]
> Note content with **formatting** possible.

> [!WARNING]
> Warning content.
```

**Supported types:** `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`

### Horizontal Rules

Horizontal separators (`---`, `***`, or `___`) create a dividing line:

---

### Links

Links are rendered as real clickable hyperlinks in the Word document, with standard styling (blue underlined). They work in paragraphs AND in tables.

Visit the [GitHub repository](https://github.com/mmaudet/md2office) for more information.

## Available Templates

md2office includes two ready-to-use templates:

| Template | Description | Main Styles |
|----------|-------------|-------------|
| `professional` | Clean business template with blue accents | Code Block, Body Text |
| `linagora` | LINAGORA corporate template with red branding | Code, Text body |

### Using Templates

```bash
# List available templates
md2office templates

# Use a specific template
md2office convert document.md -t professional
md2office convert document.md -t linagora

# Add a custom template
md2office template-add my-template.docx --name corporate

# Remove a template
md2office template-remove corporate
```

## Style Mapping

md2office uses a mapping system between Markdown elements and Word styles. Understanding this mapping is essential for creating custom templates.

### Default Mapping Table

| Markdown Element | Configured Style | Fallback |
|------------------|------------------|----------|
| `# Title` | Heading 1 | - |
| `## Title` | Heading 2 | - |
| `### Title` | Heading 3 | - |
| `#### Title` | Heading 4 | - |
| `##### Title` | Heading 5 | - |
| `###### Title` | Heading 6 | - |
| Paragraph | Text body | Body Text, Normal |
| `` `code` `` | Code in line | Code Char |
| Code block | Code | Code Block |
| `- item` | List 1 | List Bullet |
| `1. item` | Numbering 1 | List Number |
| `> quote` | Quote | - |

### Inline Formatting

Inline formatting (bold, italic, etc.) is applied directly to characters via Word font properties, independent of paragraph style.

## Cross-Template Compatibility

md2office automatically handles style naming differences between templates through an intelligent fallback system.

### How It Works

When a configured style doesn't exist in the template, md2office automatically tries alternatives:

| Configured Style | Alternatives Tried |
|------------------|-------------------|
| `Code` | Code → Code Block |
| `Code Block` | Code Block → Code |
| `Text body` | Text body → Body Text → Normal |
| `Body Text` | Body Text → Text body → Normal |
| `List 1` | List 1 → List Bullet → List Paragraph |
| `Numbering 1` | Numbering 1 → List Number → List Paragraph |

### Practical Example

With configuration `code.block: "Code"`:
- **LINAGORA Template**: Uses "Code" style (exists)
- **Professional Template**: Falls back to "Code Block" (exists)

This compatibility allows using a single configuration file for multiple templates.

## Creating Custom Templates

For best results, your DOCX template should define appropriate styles.

### Required Styles

Your template should include at minimum these styles:

1. **Heading 1 through Heading 6** - For headings
2. **Normal** or **Text body** - For paragraphs
3. **Code** or **Code Block** - For code blocks
4. **List Bullet** or **List 1** - For bullet lists
5. **List Number** or **Numbering 1** - For numbered lists
6. **Quote** - For blockquotes

### Step-by-Step Creation

1. **Open Word/LibreOffice** and create a new document
2. **Define styles** via the Styles panel:
   - Right-click on a style → Modify
   - Configure font, size, color, spacing
3. **Add headers/footers** with variables `{{title}}`, `{{date}}`
4. **Test your template** with a simple Markdown document
5. **Save** in `.docx` format
6. **Add to md2office**:
   ```bash
   md2office template-add my-template.docx --name custom
   ```

### Recommended Style Configuration

#### Heading 1
- Font: Liberation Sans, 16pt
- Color: Red (#c00000) or Blue (#1B4F72)
- Spacing before: 12pt, after: 6pt

#### Heading 2
- Font: Liberation Sans, 15pt
- Color: Dark red (#8f0a22) or Blue (#1F618D)
- Spacing before: 10pt, after: 5pt

#### Text body / Normal
- Font: Liberation Sans, 12pt
- Color: Black (#000000)
- Line spacing: 1.15
- Spacing after: 6pt

#### Code / Code Block
- Font: Liberation Mono, 9pt
- Alignment: **Left** (important!)
- Background: Light gray (#F5F5F5)

#### Quote
- Font: Liberation Sans, 11pt, italic
- Color: Gray (#555555)
- Left border
- Indent: 0.5"

## Template Variables

md2office supports variable injection in templates via Jinja2 syntax.

### Available Variables

Variables can be placed in:
- Markdown document body
- Template headers and footers
- Document properties

### Syntax

```
{{variable_name}}
```

### Usage Example

**In Markdown:**
```markdown
# Report for {{customer}}

Document prepared by {{author}} on {{date}}.
```

**Command:**
```bash
md2office convert doc.md \
  -v customer="Acme Corp" \
  -v author="John Doe" \
  -v date="January 18, 2026"
```

### LINAGORA Template Variables

| Variable | Location | Description |
|----------|----------|-------------|
| `{{title}}` | Header | Document title |
| `{{subtitle}}` | Header | Subtitle |
| `{{date}}` | Header/Footer | Document date |
| `{{author}}` | Footer | Author |
| `{{customer}}` | Body | Customer name |
| `{{project}}` | Body | Project name |
| `{{version}}` | Footer | Document version |
| `{{classification}}` | Footer | Classification (Confidential, Public, etc.) |

## REST API

md2office exposes a REST API for integration into automated workflows.

### Starting the Server

```bash
# Simple start
md2office serve --port 8080

# With auto-reload (development)
md2office serve --port 8080 --reload
```

### Endpoints

#### Markdown Conversion

**POST /api/v1/convert**

```bash
# With file
curl -X POST http://localhost:8080/api/v1/convert \
  -F "file=@document.md" \
  -F "template=professional" \
  -o output.docx

# With JSON
curl -X POST http://localhost:8080/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Hello\n\nWorld",
    "template": "professional",
    "variables": {"author": "John"}
  }' \
  --output output.docx
```

#### Template Management

```bash
# List templates
curl http://localhost:8080/api/v1/templates

# Upload a template
curl -X POST http://localhost:8080/api/v1/templates \
  -F "file=@my_template.docx" \
  -F "name=corporate"

# Delete
curl -X DELETE http://localhost:8080/api/v1/templates/corporate
```

#### Health Check

```bash
curl http://localhost:8080/api/v1/health
```

## Advanced Configuration

### Main Configuration File

**config/styles-mapping.yaml:**

```yaml
# Heading mapping
headings:
  h1: "Heading 1"
  h2: "Heading 2"
  h3: "Heading 3"
  h4: "Heading 4"
  h5: "Heading 5"
  h6: "Heading 6"

# Paragraph mapping
paragraph:
  normal: "Text body"
  quote: "Quote"

# Code mapping
code:
  inline: "Code in line"
  block: "Code"

# List mapping
list_styles:
  bullet: "List 1"
  number: "Numbering 1"

# Table configuration
table:
  style: "Table Grid"
  header_bg: "c00d2d"       # Header background color
  header_text: "FFFFFF"     # Header text color
  alternating_rows: true    # Alternating rows
  alt_row_bg: "F9F9F9"      # Alternating row color

# Admonition configuration
admonitions:
  NOTE:
    icon: "i"
    color: "0969DA"
    bg: "DDF4FF"
  TIP:
    icon: "tip"
    color: "1A7F37"
    bg: "DCFFE4"
  IMPORTANT:
    icon: "!"
    color: "8250DF"
    bg: "FBEFFF"
  WARNING:
    icon: "warn"
    color: "9A6700"
    bg: "FFF8C5"
  CAUTION:
    icon: "x"
    color: "CF222E"
    bg: "FFEBE9"
```

## Troubleshooting

### Common Errors

#### TemplateError: Template Not Found

**Error Message:**
```
TemplateError: Template 'my-template' not found
```

**Cause:** The specified template doesn't exist in md2office's template directory.

**Solutions:**
1. List available templates:
   ```bash
   md2office templates
   ```
2. Use a built-in template (`professional` or `linagora`):
   ```bash
   md2office convert document.md -t professional
   ```
3. Add your custom template:
   ```bash
   md2office template-add my-template.docx --name my-template
   ```

#### ParserError: Invalid Markdown Syntax

**Error Message:**
```
ParserError: Failed to parse Markdown document
```

**Cause:** The Markdown file contains syntax that cannot be parsed correctly.

**Solutions:**
1. Check for malformed tables (missing pipes `|` or inconsistent column counts)
2. Verify admonition syntax: `> [!NOTE]` (must be on separate line)
3. Ensure code blocks have closing triple backticks
4. Test with a minimal Markdown file to isolate the issue

**Common parsing issues:**
- Unmatched table columns: `| A | B |` vs `| X | Y | Z |`
- Missing newline before admonitions
- Unclosed inline code: `` `code without closing backtick``

#### BuilderError: DOCX Generation Failed

**Error Message:**
```
BuilderError: Failed to build DOCX document
```

**Cause:** An error occurred while constructing the Word document.

**Solutions:**
1. Verify the template file is a valid `.docx` file (not corrupted)
2. Check that template styles referenced in `config/styles-mapping.yaml` exist
3. Try with a built-in template to rule out template issues
4. Check for extremely large tables or deeply nested lists

#### ValidationError: Invalid Input

**Error Message:**
```
ValidationError: Invalid input parameters
```

**Cause:** Input validation failed (e.g., invalid file path, missing required variables).

**Solutions:**
1. Verify input file exists and is readable:
   ```bash
   ls -la document.md
   ```
2. Check file extension is `.md` or `.markdown`
3. Ensure all required variables are provided:
   ```bash
   md2office convert doc.md -v title="My Title" -v author="John Doe"
   ```

#### ConfigError: Configuration Invalid

**Error Message:**
```
ConfigError: Invalid configuration in styles-mapping.yaml
```

**Cause:** The configuration file has syntax errors or invalid values.

**Solutions:**
1. Validate YAML syntax using an online validator
2. Check for proper indentation (use spaces, not tabs)
3. Verify color codes are valid hex values (e.g., `"FF0000"`, not `"#FF0000"`)
4. Restore default configuration:
   ```bash
   git checkout config/styles-mapping.yaml
   ```

#### StorageError: File Access Failed

**Error Message:**
```
StorageError: Failed to write output file
```

**Cause:** Cannot write to the output location (permissions, disk space, locked file).

**Solutions:**
1. Check write permissions on output directory:
   ```bash
   ls -ld /path/to/output/
   ```
2. Verify sufficient disk space:
   ```bash
   df -h
   ```
3. Close the output file if open in Word/LibreOffice
4. Try writing to a different location:
   ```bash
   md2office convert doc.md -o ~/Desktop/output.docx
   ```

### Styles Not Applied

**Problem:** Document uses "Normal" instead of expected styles.

**Solutions:**
1. Verify your template contains the required styles
2. Style names are case-sensitive
3. md2office automatically tries alternatives (see [Cross-Template Compatibility](#cross-template-compatibility))

### Code Text is Justified

**Problem:** Code blocks appear with justified text instead of left-aligned.

**Solution:** This issue was fixed in version 0.1.0. md2office now forces left alignment on all code blocks.

### Lists Don't Have Bullets

**Problem:** Lists appear without bullets or numbers.

**Solution:** md2office uses text prefixes (`-` or `1.`) rather than native Word bullets for consistent rendering across all templates.

### Links Aren't Clickable

**Problem:** Links appear blue but aren't clickable.

**Solution:** Since version 0.1.0, links are converted to real Word hyperlinks. Make sure you're using the latest version.

### Admonitions Not Vertically Centered

**Problem:** Text in admonitions isn't vertically centered in the cell.

**Solution:** This issue was fixed in version 0.1.0 by removing cell margins and setting paragraph spacing to 0.

## Support

| Resource | Link |
|----------|------|
| GitHub Issues | [github.com/mmaudet/md2office/issues](https://github.com/mmaudet/md2office/issues) |
| Documentation | [github.com/mmaudet/md2office](https://github.com/mmaudet/md2office) |
| Contributing Guide | [CONTRIBUTING.md](../CONTRIBUTING.md) |

## License

md2office is distributed under the Apache 2.0 license. See the [LICENSE](../LICENSE) file for details.
