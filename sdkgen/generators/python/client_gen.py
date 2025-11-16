"""Python Client dataclass generator."""

from dataclasses import dataclass

from sdkgen.core.ir import ClientConfig
from sdkgen.core.ir import Namespace


@dataclass
class PythonClientGenerator:
    """Generates Python Client dataclass."""

    def generate(self, client: ClientConfig, namespaces: list[Namespace], package_name: str) -> str:
        """
        Generate client.py file content.

        Args:
            client: Client configuration
            namespaces: List of namespaces
            package_name: Package name for imports

        Returns:
            Python source code
        """
        return "\n".join(
            [
                *self.generate_imports(namespaces, package_name),
                "",
                "",
                *self.generate_client_class(client, namespaces),
            ]
        )

    def generate_imports(self, namespaces: list[Namespace], package_name: str) -> list[str]:
        """Generate import statements."""
        imports = [
            "from __future__ import annotations",
            "",
            "import os",
            "from copy import deepcopy",
            "from dataclasses import dataclass",
            "from dataclasses import field",
            "from typing import Any",
            "",
            "import httpx",
        ]

        # Import namespace classes
        imports.extend(
            [
                f"from {package_name}.resources.{ns.name} import {ns.name.capitalize()}"
                for ns in namespaces
            ]
        )

        return imports

    def generate_client_class(self, client: ClientConfig, namespaces: list[Namespace]) -> list[str]:
        """Generate Client dataclass."""
        lines: list[str] = []

        lines.append("@dataclass")
        lines.append("class Client:")
        lines.append('    """')
        lines.append("    Async client for API.")
        lines.append("")
        lines.append("    Configuration is read from environment variables by default:")

        lines.extend([f"    - {env_var.name}: {env_var.maps_to}" for env_var in client.env_vars])

        lines.append('    """')
        lines.append("")

        # Properties
        lines.append('    base_url: str = ""')
        lines.append('    api_key: str = ""')
        lines.append("    timeout: float = 600.0")
        lines.append("    headers: dict[str, str] = field(default_factory=dict)")
        lines.append("")

        # __post_init__
        lines.extend(self.generate_post_init(client))
        lines.append("")

        # Namespace properties
        for ns in namespaces:
            lines.extend(self.generate_namespace_property(ns))
            lines.append("")

        # Utility methods
        for method in client.utility_methods:
            lines.extend(self.generate_utility_method(method))
            lines.append("")

        # Request methods
        lines.extend(self.generate_request_method())
        lines.append("")
        lines.extend(self.generate_request_raw_method())
        lines.append("")
        lines.extend(self.generate_request_multipart_method())

        return lines

    def generate_post_init(self, client: ClientConfig) -> list[str]:
        """Generate __post_init__ method."""
        lines = [
            "    def __post_init__(self):",
            '        self.base_url = self.base_url or os.getenv("BASE_URL", "")',
            '        self.api_key = self.api_key or os.getenv("API_KEY", "")',
            "        if not self.base_url:",
            '            raise ValueError("Either pass a base_url parameter or set $BASE_URL!")',
            "        if not self.api_key:",
            '            raise ValueError("Either pass an api_key parameter or set $API_KEY")',
            '        self.base_url = self.base_url.rstrip("/")',
            '        self.headers["Authorization"] = f"Bearer {self.api_key}"',
        ]
        return lines

    def generate_namespace_property(self, ns: Namespace) -> list[str]:
        """Generate namespace property."""
        ns_class = ns.name.capitalize()
        lines = [
            "    @property",
            f"    def {ns.name}(self) -> {ns_class}:",
            f'        """Access {ns.name} API resources."""',
            f'        ns_client = self.with_namespace("{ns.path_prefix}")',
            f"        return {ns_class}(client=ns_client)",
        ]
        return lines

    def generate_utility_method(self, method) -> list[str]:
        """Generate utility method."""
        if method.template == "copy_with_overrides":
            return self.generate_with_options()
        if method.template == "copy_with_path_prefix":
            return self.generate_with_namespace()
        return []

    def generate_with_options(self) -> list[str]:
        """Generate with_options method."""
        lines = [
            "    def with_options(",
            '        self, api_key: str = "", timeout: float = 0.0, headers: dict[str, str] | None = None',
            '    ) -> "Client":',
            '        """Create a new client with updated options."""',
            "        return Client(",
            "            base_url=self.base_url,",
            "            api_key=api_key or self.api_key,",
            "            timeout=timeout or self.timeout,",
            "            headers=headers or deepcopy(self.headers),",
            "        )",
        ]
        return lines

    def generate_with_namespace(self) -> list[str]:
        """Generate with_namespace method."""
        lines = [
            '    def with_namespace(self, namespace: str) -> "Client":',
            '        """Create a new client with base_url + namespace."""',
            "        return Client(",
            '            base_url=f"{self.base_url}{namespace}",',
            "            api_key=self.api_key,",
            "            timeout=self.timeout,",
            "            headers=deepcopy(self.headers),",
            "        )",
        ]
        return lines

    def generate_request_method(self) -> list[str]:
        """Generate request method."""
        lines = [
            "    async def request(",
            "        self,",
            "        method: str,",
            "        path: str,",
            "        params: dict[str, Any] | None = None,",
            "        json: dict[str, Any] | None = None,",
            "        timeout: float = 0.0,",
            "    ) -> Any:",
            '        """Make an HTTP request to the API."""',
            '        url = f"{self.base_url}{path}"',
            "        request_headers = dict(self.headers)",
            '        request_headers["Content-Type"] = "application/json"',
            "        timeout_value = timeout or self.timeout or 30.0",
            "",
            "        async with httpx.AsyncClient(timeout=timeout_value) as client:",
            "            response = await client.request(",
            "                method=method, url=url, params=params, json=json, headers=request_headers",
            "            )",
            "",
            "            response.raise_for_status()",
            "",
            "            if response.status_code == 204:",
            "                return None",
            "",
            "            return response.json()",
        ]
        return lines

    def generate_request_raw_method(self) -> list[str]:
        """Generate request_raw method."""
        return [
            "    async def request_raw(",
            "        self,",
            "        method: str,",
            "        path: str,",
            "        params: dict[str, Any] | None = None,",
            "        json: dict[str, Any] | None = None,",
            "        timeout: float = 0.0,",
            "    ) -> bytes:",
            '        """Make an HTTP request and return raw bytes content."""',
            '        url = f"{self.base_url}{path}"',
            "        request_headers = dict(self.headers)",
            '        request_headers["Content-Type"] = "application/json"',
            "        timeout_value = timeout or self.timeout or 30.0",
            "",
            "        async with httpx.AsyncClient(timeout=timeout_value) as client:",
            "            response = await client.request(",
            "                method=method, url=url, params=params, json=json, headers=request_headers",
            "            )",
            "",
            "            response.raise_for_status()",
            "",
            "            return response.content",
        ]

    def generate_request_multipart_method(self) -> list[str]:
        """Generate request_multipart method for file uploads."""
        return [
            "    async def request_multipart(",
            "        self,",
            "        method: str,",
            "        path: str,",
            "        files: dict[str, bytes] | None = None,",
            "        data: dict[str, Any] | None = None,",
            "        timeout: float = 0.0,",
            "    ) -> Any:",
            '        """Make multipart/form-data request for file uploads."""',
            '        url = f"{self.base_url}{path}"',
            "        timeout_value = timeout or self.timeout or 30.0",
            "",
            "        async with httpx.AsyncClient(timeout=timeout_value) as client:",
            "            response = await client.request(",
            "                method=method,",
            "                url=url,",
            "                files=files,",
            "                data=data,",
            "                headers=self.headers,",
            "            )",
            "",
            "            response.raise_for_status()",
            "",
            "            return response.json()",
        ]
