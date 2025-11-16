"""Python TypedDict models generator."""

import keyword
from dataclasses import dataclass
from dataclasses import field

from sdkgen.core.ir import Model
from sdkgen.core.ir import TypeRegistry
from sdkgen.core.type_mapper import TypeMapper


@dataclass
class PythonModelsGenerator:
    """Generates Python TypedDict model definitions."""

    type_mapper: TypeMapper = field(default_factory=TypeMapper)

    def generate(self, types: TypeRegistry) -> str:
        """
        Generate models.py file content.

        Args:
            types: Type registry with all models

        Returns:
            Python source code
        """
        lines: list[str] = []

        # File docstring
        lines.append('"""Type definitions for SDK."""')
        lines.append("")

        # Imports
        lines.extend(self.generate_imports(types))
        lines.append("")
        lines.append("")

        # Generate each model
        for model in types.models:
            lines.extend(self.generate_model(model))
            lines.append("")
            lines.append("")

        return "\n".join(lines)

    def generate_imports(self, types: TypeRegistry) -> list[str]:
        """Generate import statements."""
        imports = [
            "from __future__ import annotations",
            "",
            "from typing import Any",
            "from typing import Literal",
            "from typing import NotRequired",
            "from typing import TypedDict",
        ]

        # Add enum imports if we have enums
        if types.enums:
            imports.append("from enum import Enum")

        return imports

    def generate_model(self, model: Model) -> list[str]:
        """Generate a TypedDict model."""
        lines: list[str] = []

        # Class definition
        lines.append(f"class {model.name}(TypedDict):")

        # Docstring
        if model.description:
            lines.append(f'    """{model.description}"""')
            lines.append("")

        # Properties
        if not model.properties:
            lines.append("    pass")
            return lines

        for prop in model.properties:
            # Determine field name based on model's field_naming
            base_field_name = (
                prop.python_name if model.field_naming == "snake_case" else prop.api_name
            )

            # Sanitize Python keywords by appending underscore
            field_name = (
                f"{base_field_name}_" if keyword.iskeyword(base_field_name) else base_field_name
            )

            # Generate type hint
            type_hint = self.type_mapper.get_python_type_hint(prop.type)

            # Wrap with NotRequired if not required
            type_hint = f"NotRequired[{type_hint}]" if not prop.required else type_hint

            # Add single-line description as comment (sanitize for inline use)
            comment = (
                f"  # {prop.description.split(chr(10))[0].replace(chr(34), chr(39))[:100]}"
                if prop.description
                else ""
            )

            lines.append(f"    {field_name}: {type_hint}{comment}")

        return lines
