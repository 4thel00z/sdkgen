"""Main Python SDK generator coordinator."""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from sdkgen.core.ir import SDKProject
from sdkgen.generators.python.client_gen import PythonClientGenerator
from sdkgen.generators.python.converters_gen import PythonConvertersGenerator
from sdkgen.generators.python.enums_gen import PythonEnumsGenerator
from sdkgen.generators.python.models_gen import PythonModelsGenerator
from sdkgen.generators.python.namespace_gen import PythonNamespaceGenerator
from sdkgen.generators.python.resources_gen import PythonResourcesGenerator
from sdkgen.generators.python.utils_gen import PythonUtilsGenerator


@dataclass
class PythonGenerator:
    """Main coordinator for Python SDK generation."""

    output_dir: Path
    package_name: str
    models_gen: PythonModelsGenerator = field(default_factory=PythonModelsGenerator)
    enums_gen: PythonEnumsGenerator = field(default_factory=PythonEnumsGenerator)
    converters_gen: PythonConvertersGenerator = field(default_factory=PythonConvertersGenerator)
    client_gen: PythonClientGenerator = field(default_factory=PythonClientGenerator)
    resources_gen: PythonResourcesGenerator = field(default_factory=PythonResourcesGenerator)
    namespace_gen: PythonNamespaceGenerator = field(default_factory=PythonNamespaceGenerator)
    utils_gen: PythonUtilsGenerator = field(default_factory=PythonUtilsGenerator)

    async def generate(self, project: SDKProject) -> None:
        """
        Generate complete Python SDK.

        Args:
            project: SDK project IR
        """
        # Create output directories
        self.create_directories()

        # Generate files
        self.generate_init_files()
        self.generate_models(project)
        self.generate_client(project)
        self.generate_utils()
        self.generate_namespaces(project)
        self.generate_resources(project)
        self.generate_pyproject_toml(project)
        self.generate_readme(project)

    def create_directories(self) -> None:
        """Create necessary directories."""
        package_dir = self.output_dir / self.package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (package_dir / "resources").mkdir(exist_ok=True)

    def generate_init_files(self) -> None:
        """Generate __init__.py files."""
        package_dir = self.output_dir / self.package_name

        # Main __init__.py
        init_content = [
            f'"""SDK for {self.package_name}."""',
            "",
            f"from {self.package_name}.client import Client",
            "",
            '__all__ = ["Client"]',
        ]
        self.write_file(package_dir / "__init__.py", "\n".join(init_content))

        # resources/__init__.py
        resources_init = ['"""API resources."""']
        self.write_file(package_dir / "resources" / "__init__.py", "\n".join(resources_init))

    def generate_models(self, project: SDKProject) -> None:
        """Generate models.py file."""
        package_dir = self.output_dir / self.package_name

        content = "\n\n".join(
            filter(
                None,
                [
                    self.models_gen.generate(project.types),
                    self.enums_gen.generate(project.types) if project.types.enums else None,
                    self.converters_gen.generate(project.utilities)
                    if project.utilities.converters
                    else None,
                ],
            )
        )

        self.write_file(package_dir / "models.py", content)

    def generate_client(self, project: SDKProject) -> None:
        """Generate client.py file."""
        package_dir = self.output_dir / self.package_name

        content = self.client_gen.generate(project.client, project.namespaces, self.package_name)

        self.write_file(package_dir / "client.py", content)

    def generate_utils(self) -> None:
        """Generate utils.py file."""
        package_dir = self.output_dir / self.package_name

        content = self.utils_gen.generate()
        self.write_file(package_dir / "utils.py", content)

    def generate_namespaces(self, project: SDKProject) -> None:
        """Generate namespace aggregator files (v1.py, beta.py, etc.)."""
        package_dir = self.output_dir / self.package_name / "resources"

        for namespace in project.namespaces:
            content = self.namespace_gen.generate(namespace, project, self.package_name)
            filename = f"{namespace.name}.py"
            self.write_file(package_dir / filename, content)

    def generate_resources(self, project: SDKProject) -> None:
        """Generate resource files."""
        package_dir = self.output_dir / self.package_name / "resources"

        for resource in project.resources:
            content = self.resources_gen.generate(resource, self.package_name)

            # Use lowercase filename
            filename = f"{resource.name.lower()}.py"
            self.write_file(package_dir / filename, content)

    def generate_pyproject_toml(self, project: SDKProject) -> None:
        """Generate pyproject.toml file."""
        content = f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{self.package_name}"
version = "{project.metadata.version}"
description = "{project.metadata.description}"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.7.0",
    "mypy>=1.13.0",
]

[tool.hatch.build.targets.wheel]
packages = ["{self.package_name}"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM", "TCH", "PTH", "RUF", "TID", "PL"]
ignore = ["E501", "PLR0913", "PLR2004", "PLR0912"]

[tool.ruff.lint.isort]
known-first-party = ["{self.package_name}"]
force-single-line = true
lines-after-imports = 2

[tool.mypy]
python_version = "3.12"
warn_return_any = false
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
"""
        self.write_file(self.output_dir / "pyproject.toml", content)

    def generate_readme(self, project: SDKProject) -> None:
        """Generate README.md file."""
        content = f"""# {self.package_name}

{project.metadata.description}

## Installation

```bash
pip install {self.package_name}
```

## Usage

```python
from {self.package_name} import Client

# Initialize client
client = Client(
    base_url="{project.metadata.base_url}",
    api_key="your-api-key"
)

# Use the SDK
# (Add example usage here)
```

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format .

# Type check
mypy {self.package_name}
```

## License

{project.metadata.license or "MIT"}
"""
        self.write_file(self.output_dir / "README.md", content)

    def write_file(self, path: Path, content: str) -> None:
        """
        Write content to file.

        Args:
            path: File path
            content: File content
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
