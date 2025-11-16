"""Python namespace aggregator generator."""

from dataclasses import dataclass

from sdkgen.core.ir import Namespace
from sdkgen.core.ir import SDKProject


@dataclass
class PythonNamespaceGenerator:
    """Generates namespace aggregator classes (e.g., V1, Beta)."""

    def generate(self, namespace: Namespace, project: SDKProject, package_name: str) -> str:
        """
        Generate a namespace aggregator file.

        Args:
            namespace: Namespace definition
            project: Full SDK project for finding resources
            package_name: Package name for imports

        Returns:
            Python source code
        """
        # Find all resources in this namespace
        namespace_resources = [
            resource
            for resource in project.resources
            if resource.namespace == namespace.name
            or (not resource.namespace and namespace.name == "v1")
        ]

        # Generate imports
        import_lines = [
            "from __future__ import annotations",
            "",
            "from dataclasses import dataclass",
            "from typing import TYPE_CHECKING",
            "",
            "if TYPE_CHECKING:",
            f"    from {package_name}.client import Client",
            "",
            *[
                f"from {package_name}.resources.{resource.name.lower()} import {resource.name}"
                for resource in namespace_resources
            ],
        ]

        # Generate namespace class - openapi pattern with property accessors
        class_name = namespace.name.capitalize()

        class_lines = [
            "@dataclass",
            f"class {class_name}:",
            f'    """{namespace.name.upper()} API namespace."""',
            "",
            '    client: "Client"',
            "",
            *[
                item
                for resource in namespace_resources
                for item in [
                    "    @property",
                    f"    def {resource.name.lower()}(self) -> {resource.name}:",
                    f'        """Access {resource.name} operations."""',
                    f"        return {resource.name}(client=self.client)",
                    "",
                ]
            ],
        ]

        return "\n".join([*import_lines, "", "", *class_lines])
