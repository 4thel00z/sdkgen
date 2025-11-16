"""Tests for OpenAPI parser."""

import pytest

from sdkgen.core.parser import OpenAPIParser


@pytest.fixture
def simple_spec():
    """Simple OpenAPI spec for testing."""
    return {"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}


@pytest.mark.asyncio
async def test_parser_validates_spec(simple_spec):
    """Test that parser validates basic spec structure."""
    parser = OpenAPIParser()
    parser.validate_spec(simple_spec)


@pytest.mark.asyncio
async def test_parser_rejects_invalid_version():
    """Test that parser rejects invalid OpenAPI versions."""
    parser = OpenAPIParser()

    invalid_spec = {"openapi": "2.0", "info": {"title": "Test", "version": "1.0.0"}}

    with pytest.raises(ValueError, match="Unsupported OpenAPI version"):
        parser.validate_spec(invalid_spec)


@pytest.mark.asyncio
async def test_parser_extracts_metadata(simple_spec):
    """Test metadata extraction."""
    parser = OpenAPIParser()
    metadata = parser.extract_metadata(simple_spec)

    assert metadata["title"] == "Test API"
    assert metadata["version"] == "1.0.0"
