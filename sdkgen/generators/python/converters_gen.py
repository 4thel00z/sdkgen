"""Python converter functions generator."""

from dataclasses import dataclass

from sdkgen.core.ir import Converter
from sdkgen.core.ir import UtilityConfig


@dataclass
class PythonConvertersGenerator:
    """Generates Python converter functions for snake_case ↔ camelCase."""

    def generate(self, utilities: UtilityConfig) -> str:
        """
        Generate converter functions.

        Args:
            utilities: Utility config with converters

        Returns:
            Python source code
        """
        return "\n\n".join(
            ["\n".join(self.generate_converter(converter)) for converter in utilities.converters]
        )

    def generate_converter(self, converter: Converter) -> list[str]:
        """Generate a single converter function."""
        # Function signature
        desc = (
            converter.description
            or f"Convert {converter.input_type} (snake_case) to API format (camelCase)."
        )

        # Build dict items with conditional dict pattern
        dict_items = []
        for conv in converter.conversions:
            if conv.conditional_omit:
                # Optional field - conditional pattern: **({} if not value else {"key": value})
                value_expr = (
                    f'dict(data["{conv.from_name}"])'
                    if conv.nested_convert
                    else f'data["{conv.from_name}"]'
                )
                dict_items.append(
                    f'        **({{}} if not data.get("{conv.from_name}") else {{"{conv.to_name}": {value_expr}}}),'
                )
            else:
                # Required field
                value_expr = (
                    f'dict(data["{conv.from_name}"])'
                    if conv.nested_convert
                    else f'data["{conv.from_name}"]'
                )
                dict_items.append(f'        "{conv.to_name}": {value_expr},')

        return [
            f"def {converter.name}(data: {converter.input_type}) -> dict[str, Any]:",
            f'    """{desc}"""',
            "    return {",
            *dict_items,
            "    }",
        ]
