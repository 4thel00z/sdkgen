"""Python converter functions generator."""

from dataclasses import dataclass

from sdkgen.core.ir import Converter
from sdkgen.core.ir import FieldConversion
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
        return "\n\n".join([
            "\n".join(self.generate_converter(converter))
            for converter in utilities.converters
        ])

    def generate_converter(self, converter: Converter) -> list[str]:
        """Generate a single converter function."""
        # Function signature
        desc = converter.description or f"Convert {converter.input_type} (snake_case) to API format (camelCase)."

        # Build dict items on single lines matching pharia pattern
        dict_items = []
        for conv in converter.conversions:
            if conv.conditional_omit:
                # Optional field - use pharia pattern: **({} if not value else {"key": value})
                # Check value truthiness, not key existence
                if conv.nested_convert:
                    dict_items.append(
                        '        **({} if not data.get("' + conv.from_name + '") else {"' + conv.to_name + '": dict(data["' + conv.from_name + '"])}), '
                    )
                else:
                    dict_items.append(
                        '        **({} if not data.get("' + conv.from_name + '") else {"' + conv.to_name + '": data["' + conv.from_name + '"]}),  '
                    )
            else:
                # Required field
                if conv.nested_convert:
                    dict_items.append('        "' + conv.to_name + '": dict(data["' + conv.from_name + '"]),')
                else:
                    dict_items.append('        "' + conv.to_name + '": data["' + conv.from_name + '"],')
        
        # Remove trailing spaces
        dict_items = [item.rstrip() for item in dict_items]

        return [
            f"def {converter.name}(data: {converter.input_type}) -> dict[str, Any]:",
            f'    """{desc}"""',
            "    return {",
            *dict_items,
            "    }",
        ]

