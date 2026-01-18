"""Tests for API routes."""

from __future__ import annotations

import pytest
from litestar.testing import TestClient

from md2office.main import app


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """Test health check returns healthy status."""
        with TestClient(app=app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "version" in data


class TestConvertEndpoint:
    """Tests for conversion endpoints."""

    def test_convert_simple_markdown(self):
        """Test converting simple markdown."""
        with TestClient(app=app) as client:
            response = client.post(
                "/api/v1/convert",
                json={
                    "markdown": "# Hello\n\nWorld",
                    "filename": "test.docx",
                },
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            # Check for DOCX magic bytes
            assert response.content[:2] == b"PK"

    def test_convert_with_variables(self):
        """Test converting with template variables."""
        with TestClient(app=app) as client:
            response = client.post(
                "/api/v1/convert",
                json={
                    "markdown": "# {{title}}\n\nBy {{author}}",
                    "variables": {"title": "Test", "author": "Tester"},
                    "filename": "test.docx",
                },
            )
            assert response.status_code == 200


class TestTemplatesEndpoint:
    """Tests for template management endpoints."""

    def test_list_templates(self):
        """Test listing templates."""
        with TestClient(app=app) as client:
            response = client.get("/api/v1/templates")
            assert response.status_code == 200
            data = response.json()
            assert "templates" in data
            assert "count" in data
            assert isinstance(data["templates"], list)
