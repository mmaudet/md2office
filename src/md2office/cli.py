"""Command-line interface for md2office."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import cyclopts

from md2office import __version__
from md2office.core.converter import Converter
from md2office.core.exceptions import Md2OfficeError
from md2office.template.storage import TemplateStorage

app = cyclopts.App(
    name="md2office",
    help="Convert Markdown to professional DOCX documents.",
    version=__version__,
)


@app.command
def convert(
    input_file: Annotated[Path, cyclopts.Parameter(help="Markdown file to convert")],
    output: Annotated[
        Path | None,
        cyclopts.Parameter(name=["--output", "-o"], help="Output DOCX file path"),
    ] = None,
    template: Annotated[
        str | None,
        cyclopts.Parameter(name=["--template", "-t"], help="Template name to use"),
    ] = None,
    template_path: Annotated[
        Path | None,
        cyclopts.Parameter(name="--template-path", help="Direct path to template file"),
    ] = None,
    var: Annotated[
        list[str] | None,
        cyclopts.Parameter(name=["--var", "-v"], help="Variable in key=value format"),
    ] = None,
) -> None:
    """Convert a Markdown file to DOCX.

    Examples:
        md2office convert README.md
        md2office convert README.md -o output.docx
        md2office convert README.md -t corporate -v author="John Doe"
    """
    # Validate input file
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    # Parse variables
    variables: dict[str, str] = {}
    if var:
        for v in var:
            if "=" in v:
                key, value = v.split("=", 1)
                variables[key.strip()] = value.strip()
            else:
                print(f"Warning: Ignoring invalid variable format: {v}", file=sys.stderr)

    # Determine output path
    if output is None:
        output = input_file.with_suffix(".docx")

    try:
        converter = Converter(
            template_name=template,
            template_path=template_path,
            variables=variables,
        )

        result = converter.convert_file(input_file, output)
        print(f"Created: {result}")

    except Md2OfficeError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


@app.command
def templates() -> None:
    """List available templates."""
    storage = TemplateStorage()
    templates_list = storage.list_templates()

    if not templates_list:
        print("No templates found.")
        print(f"Add templates to: {storage.templates_dir}")
        return

    print("Available templates:")
    print()
    for t in templates_list:
        size_kb = t["size"] / 1024
        print(f"  {t['name']:<20} ({size_kb:.1f} KB)")


@app.command(name="template-add")
def template_add(
    source: Annotated[Path, cyclopts.Parameter(help="Path to DOCX template file")],
    name: Annotated[
        str | None,
        cyclopts.Parameter(name=["--name", "-n"], help="Name for the template"),
    ] = None,
    overwrite: Annotated[
        bool,
        cyclopts.Parameter(name="--overwrite", help="Overwrite existing template"),
    ] = False,
) -> None:
    """Add a template to the template storage.

    Examples:
        md2office template-add corporate.docx
        md2office template-add ~/templates/report.docx --name quarterly
    """
    if not source.exists():
        print(f"Error: Template file not found: {source}", file=sys.stderr)
        sys.exit(1)

    try:
        storage = TemplateStorage()
        path = storage.add_template(source, name=name, overwrite=overwrite)
        print(f"Added template: {path.stem}")
    except Md2OfficeError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)


@app.command(name="template-remove")
def template_remove(
    name: Annotated[str, cyclopts.Parameter(help="Template name to remove")],
) -> None:
    """Remove a template from storage.

    Examples:
        md2office template-remove corporate
    """
    try:
        storage = TemplateStorage()
        storage.remove_template(name)
        print(f"Removed template: {name}")
    except Md2OfficeError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)


@app.command
def init() -> None:
    """Initialize md2office with default template.

    Creates the default template in the templates directory.

    Examples:
        md2office init
    """
    try:
        from md2office.template.generator import create_default_template

        path = create_default_template()
        print(f"Created default template: {path}")
        print("You can now use md2office to convert Markdown files.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@app.command
def serve(
    host: Annotated[
        str,
        cyclopts.Parameter(name=["--host", "-h"], help="Host to bind to"),
    ] = "0.0.0.0",
    port: Annotated[
        int,
        cyclopts.Parameter(name=["--port", "-p"], help="Port to listen on"),
    ] = 8080,
    reload: Annotated[
        bool,
        cyclopts.Parameter(name="--reload", help="Enable auto-reload for development"),
    ] = False,
) -> None:
    """Start the API server.

    Examples:
        md2office serve
        md2office serve --port 3000 --reload
    """
    try:
        import uvicorn

        print(f"Starting server at http://{host}:{port}")
        uvicorn.run(
            "md2office.main:app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        print("Error: uvicorn not installed. Install with: pip install litestar[standard]")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
