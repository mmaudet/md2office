"""Main application entry point for md2office API."""

from __future__ import annotations

from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin

from md2office import __version__
from md2office.api.routes import api_router

# CORS configuration
cors_config = CORSConfig(
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# OpenAPI configuration
openapi_config = OpenAPIConfig(
    title="md2office API",
    version=__version__,
    description="Convert Markdown to professional DOCX documents",
    render_plugins=[SwaggerRenderPlugin()],
)

# Create the Litestar application
app = Litestar(
    route_handlers=[api_router],
    cors_config=cors_config,
    openapi_config=openapi_config,
)


def create_app() -> Litestar:
    """Factory function for creating the application.

    Useful for testing and programmatic app creation.

    Returns:
        Configured Litestar application.
    """
    return Litestar(
        route_handlers=[api_router],
        cors_config=cors_config,
        openapi_config=openapi_config,
    )
