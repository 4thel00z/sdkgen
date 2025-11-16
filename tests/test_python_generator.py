"""Tests for Python generator."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from sdkgen.core.ir import ClientConfig
from sdkgen.core.ir import Model
from sdkgen.core.ir import Namespace
from sdkgen.core.ir import ProjectMetadata
from sdkgen.core.ir import Property
from sdkgen.core.ir import SDKProject
from sdkgen.core.ir import TypeRegistry
from sdkgen.generators.python.generator import PythonGenerator


@pytest.fixture
def minimal_project():
    """Minimal SDK project for testing."""
    return SDKProject(
        metadata=ProjectMetadata(
            name="test_sdk",
            version="1.0.0",
            description="Test SDK",
            base_url="https://api.example.com",
        ),
        types=TypeRegistry(
            models=[
                Model(
                    name="User",
                    type="object",
                    field_naming="camelCase",
                    properties=[
                        Property(
                            name="id",
                            python_name="id",
                            api_name="id",
                            type={"kind": "primitive", "primitive": "string"},
                            required=True,
                        )
                    ],
                    required=["id"],
                )
            ]
        ),
        client=ClientConfig(name="Client"),
        namespaces=[Namespace(name="v1", path_prefix="/api/v1")],
    )


@pytest.mark.asyncio
async def test_python_generator_creates_files(minimal_project):
    """Test that Python generator creates expected files."""
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generator = PythonGenerator(output_dir=output_dir, package_name="test_sdk")

        await generator.generate(minimal_project)

        # Check files exist
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "test_sdk" / "__init__.py").exists()
        assert (output_dir / "test_sdk" / "client.py").exists()
        assert (output_dir / "test_sdk" / "models.py").exists()
        assert (output_dir / "test_sdk" / "utils.py").exists()


@pytest.mark.asyncio
async def test_python_generator_creates_valid_package_structure(minimal_project):
    """Test that generated package has valid structure."""
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generator = PythonGenerator(output_dir=output_dir, package_name="test_sdk")

        await generator.generate(minimal_project)

        # Check package structure
        package_dir = output_dir / "test_sdk"
        assert package_dir.is_dir()
        assert (package_dir / "resources").is_dir()
        assert (package_dir / "resources" / "__init__.py").exists()
