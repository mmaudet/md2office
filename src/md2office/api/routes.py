"""API routes for md2office."""

from __future__ import annotations

from typing import Any

from litestar import Controller, Response, Router, delete, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from md2office import __version__
from md2office.api.models import (
    ConvertRequest,
    ErrorResponse,
    HealthResponse,
    TemplateInfo,
    TemplateListResponse,
    TemplateUploadResponse,
)
from md2office.core.converter import Converter
from md2office.core.exceptions import Md2OfficeError, TemplateError
from md2office.template.storage import TemplateStorage


class HealthController(Controller):
    """Health check endpoints."""

    path = "/health"

    @get()
    async def health_check(self) -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(status="healthy", version=__version__)


class ConvertController(Controller):
    """Conversion endpoints."""

    path = "/api/v1/convert"

    @post()
    async def convert_markdown(
        self,
        data: ConvertRequest,
    ) -> Response[bytes]:
        """Convert Markdown text to DOCX.

        Args:
            data: Conversion request with markdown content.

        Returns:
            DOCX file as binary response.
        """
        try:
            converter = Converter(
                template_name=data.template,
                variables=data.variables,
            )

            doc_bytes = converter.convert(data.markdown)
            assert isinstance(doc_bytes, bytes)

            return Response(
                content=doc_bytes,
                status_code=HTTP_200_OK,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f'attachment; filename="{data.filename}"',
                },
            )

        except Md2OfficeError as e:
            return Response(
                content=ErrorResponse(error=e.message, details=e.details),
                status_code=HTTP_400_BAD_REQUEST,
            )

    @post("/file")
    async def convert_file(
        self,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
        template: str | None = None,
        variables: str | None = None,  # JSON string
    ) -> Response[bytes]:
        """Convert an uploaded Markdown file to DOCX.

        Args:
            data: Uploaded Markdown file.
            template: Optional template name.
            variables: Optional JSON string of variables.

        Returns:
            DOCX file as binary response.
        """
        try:
            # Read uploaded file
            content = await data.read()
            markdown = content.decode("utf-8")

            # Parse variables JSON if provided
            vars_dict: dict[str, Any] | None = None
            if variables:
                import json

                vars_dict = json.loads(variables)

            converter = Converter(
                template_name=template,
                variables=vars_dict,
            )

            doc_bytes = converter.convert(markdown)
            assert isinstance(doc_bytes, bytes)

            # Generate output filename
            filename = data.filename or "document.md"
            if filename.endswith(".md"):
                filename = filename[:-3] + ".docx"
            else:
                filename = filename + ".docx"

            return Response(
                content=doc_bytes,
                status_code=HTTP_200_OK,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                },
            )

        except Md2OfficeError as e:
            return Response(
                content=ErrorResponse(error=e.message, details=e.details),
                status_code=HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                content=ErrorResponse(error=str(e)),
                status_code=HTTP_400_BAD_REQUEST,
            )


class TemplateController(Controller):
    """Template management endpoints."""

    path = "/api/v1/templates"

    @get()
    async def list_templates(self) -> TemplateListResponse:
        """List all available templates."""
        storage = TemplateStorage()
        templates = storage.list_templates()

        return TemplateListResponse(
            templates=[
                TemplateInfo(
                    name=t["name"],
                    size=t["size"],
                    modified=t["modified"],
                )
                for t in templates
            ],
            count=len(templates),
        )

    @get("/{name:str}")
    async def get_template(self, name: str) -> Response:
        """Get template information or download.

        Args:
            name: Template name.

        Returns:
            Template info or error.
        """
        try:
            storage = TemplateStorage()
            info = storage.get_template_info(name)

            return Response(
                content=TemplateInfo(
                    name=info["name"],
                    size=info["size"],
                    modified=info["modified"],
                    path=info["path"],
                ),
                status_code=HTTP_200_OK,
            )

        except TemplateError as e:
            return Response(
                content=ErrorResponse(error=e.message),
                status_code=HTTP_400_BAD_REQUEST,
            )

    @post()
    async def upload_template(
        self,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
        name: str | None = None,
        overwrite: bool = False,
    ) -> Response:
        """Upload a new template.

        Args:
            data: Uploaded DOCX template file.
            name: Optional name for the template.
            overwrite: Whether to overwrite existing.

        Returns:
            Upload status.
        """
        try:
            import tempfile
            from pathlib import Path

            # Save uploaded file temporarily
            content = await data.read()
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            try:
                storage = TemplateStorage()
                template_name = name or (data.filename.replace(".docx", "") if data.filename else None)
                path = storage.add_template(tmp_path, name=template_name, overwrite=overwrite)

                return Response(
                    content=TemplateUploadResponse(
                        success=True,
                        name=path.stem,
                        message="Template uploaded successfully",
                    ),
                    status_code=HTTP_201_CREATED,
                )
            finally:
                # Clean up temp file
                tmp_path.unlink(missing_ok=True)

        except Md2OfficeError as e:
            return Response(
                content=ErrorResponse(error=e.message),
                status_code=HTTP_400_BAD_REQUEST,
            )

    @delete("/{name:str}", status_code=HTTP_200_OK)
    async def delete_template(self, name: str) -> Response:
        """Delete a template.

        Args:
            name: Template name to delete.

        Returns:
            Deletion status.
        """
        try:
            storage = TemplateStorage()
            storage.remove_template(name)

            return Response(
                content=TemplateUploadResponse(
                    success=True,
                    name=name,
                    message="Template deleted successfully",
                ),
                status_code=HTTP_200_OK,
            )

        except TemplateError as e:
            return Response(
                content=ErrorResponse(error=e.message),
                status_code=HTTP_400_BAD_REQUEST,
            )


# Create the API router
api_router = Router(
    path="/",
    route_handlers=[
        HealthController,
        ConvertController,
        TemplateController,
    ],
)
