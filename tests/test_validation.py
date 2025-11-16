"""Tests for validating generated SDK code quality."""

import ast
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from sdkgen.core.ir_builder import IRBuilder
from sdkgen.core.parser import OpenAPIParser
from sdkgen.generators.python.generator import PythonGenerator


@pytest.mark.asyncio
async def test_generated_code_is_valid_python():
    """Test that all generated Python code is syntactically valid."""
    parser = OpenAPIParser()
    spec_path = Path(__file__).parent / "fixtures" / "openapi_specs" / "stripe.json"

    if not spec_path.exists():
        pytest.skip("Stripe spec not available")

    # Parse and build IR
    spec = await parser.parse(str(spec_path), resolve_refs=True)
    builder = IRBuilder()
    project = builder.build(spec)

    # Generate SDK
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generator = PythonGenerator(output_dir=output_dir, package_name="test_sdk")
        await generator.generate(project)

        # Validate all Python files
        python_files = list(output_dir.rglob("*.py"))
        assert len(python_files) > 0, "No Python files generated"

        errors = []
        for py_file in python_files:
            try:
                code = py_file.read_text()
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"{py_file.name}: {e}")

        assert not errors, f"Syntax errors found:\n" + "\n".join(errors)


@pytest.mark.asyncio
async def test_generated_code_imports_successfully():
    """Test that generated code can be imported."""
    parser = OpenAPIParser()
    spec_path = Path(__file__).parent / "fixtures" / "openapi_specs" / "stripe.json"

    if not spec_path.exists():
        pytest.skip("Stripe spec not available")

    spec = await parser.parse(str(spec_path), resolve_refs=True)
    builder = IRBuilder()
    project = builder.build(spec)

    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        generator = PythonGenerator(output_dir=output_dir, package_name="test_sdk")
        await generator.generate(project)

        # Check that key files exist
        assert (output_dir / "test_sdk" / "__init__.py").exists()
        assert (output_dir / "test_sdk" / "client.py").exists()
        assert (output_dir / "test_sdk" / "models.py").exists()
        assert (output_dir / "test_sdk" / "utils.py").exists()

