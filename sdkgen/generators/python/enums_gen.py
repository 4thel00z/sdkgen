"""Python Enum generator."""

from dataclasses import dataclass

from sdkgen.core.ir import TypeRegistry


@dataclass
class PythonEnumsGenerator:
    """Generates Python Enum class definitions."""

    def generate(self, types: TypeRegistry) -> str:
        """
        Generate enum definitions.

        Args:
            types: Type registry with all enums

        Returns:
            Python source code
        """
        return "\n".join(
            [
                line
                for enum in types.enums
                for line in [
                    f"class {enum.name}(str, Enum):",
                    *([f'    """{enum.description}"""', ""] if enum.description else []),
                    *[
                        item
                        for value in enum.values
                        for item in [
                            *([f"    # {value.description}"] if value.description else []),
                            f'    {value.name} = "{value.value}"'
                            if enum.base_type == "string"
                            else f"    {value.name} = {value.value}",
                        ]
                    ],
                    "",
                    "",
                ]
            ]
        )
