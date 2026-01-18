# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

md2office is a Python-based open source solution for converting Markdown files to professional Microsoft Office (DOCX) documents with corporate template support and style mapping.

## Tech Stack

- **Language**: Python 3.11+
- **API Framework**: FastAPI with Uvicorn
- **Markdown Parser**: mistune 3.x
- **DOCX Generation**: python-docx
- **Templating**: Jinja2
- **Validation**: Pydantic v2
- **CLI**: Click
- **Tests**: pytest + pytest-asyncio

## Build & Development Commands

```bash
# Install dependencies (once pyproject.toml exists)
pip install -e ".[dev]"

# Run the API server
uvicorn md2office.main:app --reload --host 0.0.0.0 --port 8080

# Run CLI
md2office convert input.md --template corporate --output output.docx

# Run tests
pytest

# Run single test file
pytest tests/test_parser/test_markdown_parser.py

# Run with coverage
pytest --cov=md2office --cov-report=html

# Docker build
docker build -t md2office .

# Docker run
docker-compose up
```

## Architecture

```
src/md2office/
├── main.py              # FastAPI entry point
├── cli.py               # Click CLI interface
├── api/                 # REST API handlers and models
├── core/                # Config, converter orchestrator, exceptions
├── parser/              # Markdown parsing (mistune-based AST)
├── builder/             # DOCX construction (python-docx)
├── template/            # Jinja2 template engine, variable injection
└── utils/               # Helper functions
```

### Key Components

1. **Markdown Parser** (`parser/`): Uses mistune with custom `DocxRenderer` that produces intermediate AST elements (not text)

2. **Template Engine** (`template/`): Handles DOCX template loading, style extraction, and `{{variable}}` injection in headers, footers, cover pages, and body

3. **DOCX Builder** (`builder/`): Constructs final document using python-docx, applies style mapping from config

4. **Style Mapper** (`builder/style_mapper.py`): Maps Markdown elements to named Word styles defined in `config/styles-mapping.yaml`

### Data Flow

```
Markdown + Variables → Parser (mistune) → AST → Builder (python-docx) → DOCX
                           ↑                        ↑
                    Template Engine ←── DOCX Template + Style Config
```

## Configuration Files

- `config/config.yaml`: Server settings, storage paths, defaults
- `config/styles-mapping.yaml`: Maps Markdown elements to Word style names, table/list formatting, admonition types

## Key Features to Implement

1. **Admonitions**: `> [!NOTE]`, `> [!WARNING]`, etc. rendered as styled tables with colored borders
2. **Tables**: Full formatting support (borders, header colors, alternating rows)
3. **Style Mapping**: All Markdown elements map to named Word styles from template
4. **Variable Injection**: Jinja2-style `{{var}}` in document metadata, headers, footers, body

## API Endpoints

- `POST /api/v1/convert` - Convert Markdown to DOCX
- `GET/POST/DELETE /api/v1/templates` - Template management
- `POST /api/v1/batch/convert` - Batch conversion
- `GET /api/v1/health` - Health check
