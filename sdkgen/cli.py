"""CLI for sdkgen."""

import asyncio
import json
from pathlib import Path

import click

from sdkgen.core.ir_builder import IRBuilder
from sdkgen.core.parser import OpenAPIParser
from sdkgen.generators.python.generator import PythonGenerator
from sdkgen.utils.name_sanitizer import sanitize_package_name


@click.group()
def cli():
    """SDKGen - Multi-language SDK generator from OpenAPI specifications."""
    pass


@cli.command()
@click.option(
    "--input", "-i", "input_path", required=True, help="Path or URL to OpenAPI specification"
)
@click.option(
    "--output", "-o", "output_path", required=True, help="Output directory for generated SDK"
)
@click.option(
    "--language", "-l", default="python", help="Target language (python, typescript, go, rust)"
)
@click.option("--package-name", "-n", help="Package name (default: from OpenAPI title)")
def generate(input_path: str, output_path: str, language: str, package_name: str | None):
    """Generate SDK from OpenAPI specification."""
    asyncio.run(generate_async(input_path, output_path, language, package_name))


async def generate_async(
    input_path: str, output_path: str, language: str, package_name: str | None
):
    """Async implementation of generate command."""
    click.echo(f"Parsing OpenAPI spec from: {input_path}")

    # Parse OpenAPI spec
    parser = OpenAPIParser()
    spec = await parser.parse(input_path, resolve_refs=True)

    click.echo("Building IR...")

    # Build IR
    builder = IRBuilder()
    project = builder.build(spec, package_name)

    # Determine package name
    if not package_name:
        package_name = sanitize_package_name(project.metadata.name)

    click.echo(f"Generating {language} SDK...")

    # Generate SDK
    if language == "python":
        output_dir = Path(output_path)
        generator = PythonGenerator(output_dir=output_dir, package_name=package_name)
        await generator.generate(project)
        click.echo(f"✓ Generated Python SDK in: {output_dir}")
    else:
        click.echo(f"Error: Language '{language}' not yet supported")
        return

    click.echo("✓ SDK generation complete!")


@cli.command()
@click.option(
    "--input", "-i", "input_path", required=True, help="Path or URL to OpenAPI specification"
)
def validate(input_path: str):
    """Validate an OpenAPI specification."""
    asyncio.run(validate_async(input_path))


async def validate_async(input_path: str):
    """Async implementation of validate command."""
    click.echo(f"Validating OpenAPI spec: {input_path}")

    try:
        parser = OpenAPIParser()
        spec = await parser.parse(input_path, resolve_refs=False)

        # Basic validation
        version = spec.get("openapi", "unknown")
        title = spec.get("info", {}).get("title", "unknown")
        paths_count = len(spec.get("paths", {}))
        schemas_count = len(spec.get("components", {}).get("schemas", {}))

        click.echo("✓ Valid OpenAPI specification!")
        click.echo(f"  Version: {version}")
        click.echo(f"  Title: {title}")
        click.echo(f"  Paths: {paths_count}")
        click.echo(f"  Schemas: {schemas_count}")

    except Exception as e:
        click.echo(f"✗ Invalid OpenAPI specification: {e}")


@cli.command()
@click.option(
    "--input", "-i", "input_path", required=True, help="Path or URL to OpenAPI specification"
)
@click.option("--output", "-o", "output_path", help="Output file for IR JSON (default: stdout)")
def show_ir(input_path: str, output_path: str | None):
    """Show intermediate representation (IR) of an OpenAPI spec."""
    asyncio.run(show_ir_async(input_path, output_path))


async def show_ir_async(input_path: str, output_path: str | None):
    """Async implementation of show-ir command."""
    click.echo(f"Parsing OpenAPI spec: {input_path}")

    # Parse and build IR
    parser = OpenAPIParser()
    spec = await parser.parse(input_path, resolve_refs=True)

    builder = IRBuilder()
    project = builder.build(spec)

    # Convert IR to dict (simplified representation)
    ir_dict = {
        "metadata": {
            "name": project.metadata.name,
            "version": project.metadata.version,
            "description": project.metadata.description,
            "base_url": project.metadata.base_url,
        },
        "namespaces": [
            {"name": ns.name, "path_prefix": ns.path_prefix} for ns in project.namespaces
        ],
        "resources": [
            {
                "name": r.name,
                "operations": [
                    {"name": op.name, "method": op.method, "path": op.path} for op in r.operations
                ],
            }
            for r in project.resources
        ],
        "models": [
            {"name": m.name, "properties_count": len(m.properties)} for m in project.types.models
        ],
        "enums": [{"name": e.name, "values_count": len(e.values)} for e in project.types.enums],
    }

    ir_json = json.dumps(ir_dict, indent=2)

    if output_path:
        Path(output_path).write_text(ir_json)
        click.echo(f"✓ IR written to: {output_path}")
    else:
        click.echo(ir_json)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
