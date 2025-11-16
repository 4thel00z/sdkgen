"""Tests for IR builder."""

import pytest

from sdkgen.core.ir_builder import IRBuilder


@pytest.fixture
def simple_spec():
    """Simple OpenAPI spec for testing."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test API", "version": "1.0.0", "description": "A test API"},
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/users": {
                "get": {
                    "tags": ["users"],
                    "operationId": "listUsers",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
                    "required": ["id", "name"],
                }
            }
        },
    }


def test_ir_builder_builds_metadata(simple_spec):
    """Test that IR builder extracts metadata correctly."""
    builder = IRBuilder()
    project = builder.build(simple_spec)

    assert project.metadata.name == "test_api"
    assert project.metadata.version == "1.0.0"
    assert project.metadata.base_url == "https://api.example.com"


def test_ir_builder_builds_models(simple_spec):
    """Test that IR builder creates models from schemas."""
    builder = IRBuilder()
    project = builder.build(simple_spec)

    assert len(project.types.models) > 0

    user_model = next((m for m in project.types.models if m.name == "User"), None)
    assert user_model is not None
    assert len(user_model.properties) == 2


def test_ir_builder_builds_resources(simple_spec):
    """Test that IR builder creates resources from paths."""
    builder = IRBuilder()
    project = builder.build(simple_spec)

    assert len(project.resources) > 0

    users_resource = next((r for r in project.resources if "user" in r.name.lower()), None)
    assert users_resource is not None
    assert len(users_resource.operations) > 0
