"""Python resource dataclasses generator."""

from dataclasses import dataclass
from dataclasses import field

from sdkgen.core.ir import Operation
from sdkgen.core.ir import Resource
from sdkgen.core.type_mapper import TypeMapper


@dataclass
class PythonResourcesGenerator:
    """Generates Python resource dataclasses with async operations."""

    type_mapper: TypeMapper = field(default_factory=TypeMapper)

    def generate(self, resource: Resource, package_name: str) -> str:
        """
        Generate a resource file.

        Args:
            resource: Resource definition
            package_name: Package name for imports

        Returns:
            Python source code
        """
        return "\n".join(
            [*self.generate_imports(package_name), "", "", *self.generate_resource_class(resource)]
        )

    def generate_imports(self, package_name: str) -> list[str]:
        """Generate import statements."""
        return [
            "from __future__ import annotations",
            "",
            "from dataclasses import dataclass",
            "from typing import TYPE_CHECKING",
            "from typing import Any",
            "",
            "if TYPE_CHECKING:",
            f"    from {package_name}.client import Client",
        ]

    def generate_resource_class(self, resource: Resource) -> list[str]:
        """Generate resource dataclass."""
        lines: list[str] = []

        lines.append("@dataclass")
        lines.append(f"class {resource.name}:")
        desc = resource.description or f"Operations for {resource.name}."
        lines.append(f'    """{desc}"""')
        lines.append("")
        lines.append('    client: "Client"')
        lines.append("")

        # Generate operations
        for operation in resource.operations:
            lines.extend(self.generate_operation(operation))
            lines.append("")

        return lines

    def generate_operation(self, operation: Operation) -> list[str]:
        """Generate an operation method."""
        # Method signature with proper parameters
        params_str = self.build_parameters(operation)

        # Determine return type
        return_type = self.get_return_type(operation)

        # Clean description
        desc = operation.description or operation.summary or f"{operation.name.title()} operation"

        # Build path with f-string interpolation
        path_with_params = self.build_path_string(operation.path, operation.path_params)

        # Build query params dict
        params_dict_lines = self.build_query_params_dict(operation.query_params)

        # Build request payload from body params
        payload_lines = self.build_request_payload(operation)

        # Determine request method based on content type
        if operation.return_format == "multipart":
            return self.generate_multipart_operation(
                operation, params_str, return_type, desc, path_with_params
            )

        request_method = "request_raw" if operation.return_format == "binary" else "request"

        return [
            f"    async def {operation.name}({params_str}) -> {return_type}:",
            f'        """{desc}"""',
            *params_dict_lines,
            *payload_lines,
            f"        return await self.client.{request_method}(",
            f'            "{operation.method}",',
            f"            {path_with_params},",
            *(["            params=params,"] if operation.query_params else []),
            *(
                ["            json=payload,"]
                if operation.body_params or operation.use_unpack_pattern
                else []
            ),
            "        )",
        ]

    def build_request_payload(self, operation: Operation) -> list[str]:
        """Build request payload from body params."""
        if operation.use_unpack_pattern:
            return ["        payload = data  # Using Unpack pattern"]

        if not operation.body_params:
            return []

        required_body = [p for p in operation.body_params if p.required]
        optional_body = [p for p in operation.body_params if not p.required]

        return [
            "        payload = {",
            *['            "' + p.api_name + '": ' + p.python_name + "," for p in required_body],
            *[
                "            **({} if not "
                + p.python_name
                + ' else {"'
                + p.api_name
                + '": '
                + p.python_name
                + "}),"
                for p in optional_body
            ],
            "        }",
        ]

    def generate_multipart_operation(
        self, operation: Operation, params_str: str, return_type: str, desc: str, path_str: str
    ) -> list[str]:
        """Generate multipart/form-data operation for file uploads."""
        # Separate file params from data params
        file_params = [p for p in operation.body_params if p.type.primitive == "bytes"]
        data_params = [p for p in operation.body_params if p.type.primitive != "bytes"]

        return [
            f"    async def {operation.name}({params_str}) -> {return_type}:",
            f'        """{desc}"""',
            *(
                [
                    "        files = {",
                    *[
                        '            "' + p.api_name + '": ' + p.python_name + ","
                        for p in file_params
                    ],
                    "        }",
                ]
                if file_params
                else []
            ),
            *(
                [
                    "        data = {",
                    *[
                        '            "' + p.api_name + '": ' + p.python_name + ","
                        for p in data_params
                        if p.required
                    ],
                    *[
                        "            **({} if not "
                        + p.python_name
                        + ' else {"'
                        + p.api_name
                        + '": '
                        + p.python_name
                        + "}),"
                        for p in data_params
                        if not p.required
                    ],
                    "        }",
                ]
                if data_params
                else []
            ),
            "        return await self.client.request_multipart(",
            f'            "{operation.method}",',
            f"            {path_str},",
            *(["            files=files,"] if file_params else []),
            *(["            data=data,"] if data_params else []),
            "        )",
        ]

    def build_query_params_dict(self, query_params: list) -> list[str]:
        """Build params dictionary matching pharia pattern."""
        if not query_params:
            return []

        # Separate required and optional
        required_params = [p for p in query_params if p.required]
        optional_params = [p for p in query_params if not p.required]

        if not optional_params:
            # All required - simple dict
            items = ['"' + p.api_name + '": ' + p.python_name for p in required_params]
            return ["        params = {" + ", ".join(items) + "}"]

        # Build conditional dict pattern: **({} if not x else {"key": x})
        dict_lines = ["        params = {"]

        # Add required params
        dict_lines.extend(
            ['            "' + p.api_name + '": ' + p.python_name + "," for p in required_params]
        )

        # Add optional params - conditional pattern: **({} if not value else {"key": value}),
        dict_lines.extend(
            [
                "            **({} if not "
                + p.python_name
                + ' else {"'
                + p.api_name
                + '": '
                + p.python_name
                + "}),"
                for p in optional_params
            ]
        )

        dict_lines.append("        }")

        return dict_lines

    def build_path_string(self, path: str, path_params: list) -> str:
        """Build path string with f-string interpolation."""
        if not path_params:
            return f'"{path}"'

        # Replace {param} with {param_python_name}
        result_path = path
        for param in path_params:
            result_path = result_path.replace(f"{{{param.name}}}", f"{{{param.python_name}}}")

        return f'f"{result_path}"'

    def build_params_dict(self, query_params: list) -> None:
        """Build params dictionary - returns None, params are built inline."""
        return None

    def get_return_type(self, operation: Operation) -> str:
        """Get return type from operation responses."""
        if operation.return_format == "binary":
            return "bytes"

        # Use extracted response type
        if operation.response_type:
            return self.type_mapper.get_python_type_hint(operation.response_type)

        # Fallback to Any only if no response type found
        return "Any"

    def build_parameters(self, operation: Operation) -> str:
        """Build parameter string for method signature."""
        # CRITICAL: Required params MUST come before optional params in Python!

        # Separate required and optional for BOTH body and query params
        required_body = [p for p in operation.body_params if p.required and p.type]
        optional_body = [p for p in operation.body_params if not p.required and p.type]
        required_query = [qp for qp in operation.query_params if qp.required and qp.type]
        optional_query = [qp for qp in operation.query_params if not qp.required and qp.type]

        params_list = [
            "self",
            # Path params (always required)
            *[path_param.python_name + ": str" for path_param in operation.path_params],
            # Required body params
            *[
                p.python_name + ": " + (self.type_mapper.get_python_type_hint(p.type) or "Any")
                for p in required_body
            ],
            # Required query params (no defaults)
            *[
                qp.python_name + ": " + (self.type_mapper.get_python_type_hint(qp.type) or "Any")
                for qp in required_query
            ],
            # Optional body params
            *[
                p.python_name
                + ": "
                + (self.type_mapper.get_python_type_hint(p.type) or "Any")
                + " | None = None"
                for p in optional_body
            ],
            # Optional query params (with defaults)
            *[
                qp.python_name
                + ": "
                + (self.type_mapper.get_python_type_hint(qp.type) or "Any")
                + " | None = None"
                for qp in optional_query
            ],
            # Request body (if using unpack pattern for model refs)
            *(["**data: Any"] if operation.use_unpack_pattern else []),
        ]

        return ", ".join(params_list)
