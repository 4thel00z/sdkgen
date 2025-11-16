"""Python utilities generator."""

from dataclasses import dataclass


@dataclass
class PythonUtilsGenerator:
    """Generates Python utility functions."""

    def generate(self) -> str:
        """
        Generate utils.py file content.

        Returns:
            Python source code
        """
        return "\n".join(
            [
                '"""Utility functions for the SDK."""',
                "",
                "from typing import Any",
                "",
                "",
                *self.generate_to_camel_case(),
                "",
                "",
                *self.generate_convert_keys(),
            ]
        )

    def generate_to_camel_case(self) -> list[str]:
        """Generate to_camel_case function."""
        return [
            "def to_camel_case(snake_str: str) -> str:",
            '    """Convert snake_case string to camelCase."""',
            '    components = snake_str.split("_")',
            '    return components[0] + "".join(x.title() for x in components[1:])',
        ]

    def generate_convert_keys(self) -> list[str]:
        """Generate convert_keys_to_camel_case function."""
        return [
            "def convert_keys_to_camel_case(data: dict[str, Any]) -> dict[str, Any]:",
            '    """',
            "    Recursively convert all dictionary keys from snake_case to camelCase.",
            '    """',
            "    if not isinstance(data, dict):",
            "        return data",
            "",
            "    result = {}",
            "    for key, value in data.items():",
            "        camel_key = to_camel_case(key)",
            "",
            "        if isinstance(value, dict):",
            "            result[camel_key] = convert_keys_to_camel_case(value)",
            "        elif isinstance(value, list):",
            "            result[camel_key] = [",
            "                convert_keys_to_camel_case(item) if isinstance(item, dict) else item",
            "                for item in value",
            "            ]",
            "        else:",
            "            result[camel_key] = value",
            "",
            "    return result",
        ]
