"""Namespace analyzer for detecting API versioning patterns."""

from dataclasses import dataclass
from typing import Any

from sdkgen.core.ir import Namespace


@dataclass
class NamespaceAnalyzer:
    """Analyzes OpenAPI specs for namespace/versioning patterns."""

    def detect_namespaces(self, spec: dict[str, Any]) -> list[Namespace]:
        """
        Detect namespaces from paths and servers.

        Args:
            spec: OpenAPI specification

        Returns:
            List of detected namespaces
        """
        namespaces: dict[str, Namespace] = {}

        # Analyze paths for version prefixes
        paths = spec.get("paths", {})
        for path in paths:
            namespace = self.extract_namespace_from_path(path)
            if namespace and namespace not in namespaces:
                namespaces[namespace] = Namespace(
                    name=namespace, path_prefix=f"/{namespace}", resources=[]
                )

        # If no namespaces detected, create default
        if not namespaces:
            # Check servers for base path
            servers = spec.get("servers", [])
            if servers and len(servers) > 0:
                server_url = servers[0].get("url", "")
                namespace = self.extract_namespace_from_url(server_url)
                if namespace:
                    namespaces[namespace] = Namespace(
                        name=namespace, path_prefix=f"/{namespace}", resources=[]
                    )

        return list(namespaces.values())

    def extract_namespace_from_path(self, path: str) -> str | None:
        """
        Extract namespace from path.

        Examples:
            /api/v1/users -> v1
            /v2/products -> v2
            /beta/features -> beta

        Args:
            path: API path

        Returns:
            Namespace name or None
        """
        parts = path.strip("/").split("/")

        # Look for version patterns
        for i, part in enumerate(parts):
            # Match v1, v2, etc.
            if part.startswith("v") and len(part) > 1 and part[1:].isdigit():
                return part

            # Match beta, alpha, etc.
            if part in ("beta", "alpha", "canary", "preview"):
                return part

            # Match api/v1 pattern
            if part == "api" and i + 1 < len(parts):
                next_part = parts[i + 1]
                if next_part.startswith("v") and next_part[1:].isdigit():
                    return next_part

        return None

    def extract_namespace_from_url(self, url: str) -> str | None:
        """
        Extract namespace from server URL.

        Args:
            url: Server URL

        Returns:
            Namespace or None
        """
        # Remove protocol
        if "://" in url:
            url = url.split("://", 1)[1]

        # Extract path
        if "/" in url:
            path = "/" + url.split("/", 1)[1]
            return self.extract_namespace_from_path(path)

        return None

    def group_paths_by_namespace(self, paths: dict[str, Any]) -> dict[str, list[str]]:
        """
        Group paths by their namespace.

        Args:
            paths: OpenAPI paths object

        Returns:
            Dictionary mapping namespace to paths
        """
        grouped: dict[str, list[str]] = {}

        for path in paths:
            namespace = self.extract_namespace_from_path(path) or "default"
            if namespace not in grouped:
                grouped[namespace] = []
            grouped[namespace].append(path)

        return grouped
