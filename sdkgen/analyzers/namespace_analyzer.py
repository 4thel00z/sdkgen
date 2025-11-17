"""Namespace analyzer for detecting API versioning patterns."""

from dataclasses import dataclass
from typing import Any

from sdkgen.core.ir import Namespace


@dataclass
class NamespaceAnalyzer:
    """Analyzes OpenAPI specs for namespace/versioning patterns.

    Detects API versioning and namespace patterns from paths and server URLs.
    Supports common patterns like v1, v2, beta, alpha, and API prefixes.
    Creates default namespaces when no explicit versioning is detected.

    This analyzer is stateless and all methods can be called independently.
    """

    def detect_namespaces(self, spec: dict[str, Any]) -> list[Namespace]:
        """Detect namespaces from paths and server URLs.

        Analyzes the OpenAPI specification to identify versioning patterns
        in API paths and server URLs. Creates Namespace objects for each
        detected version or falls back to server URL analysis if no path
        versioning is found.

        Args:
            spec: OpenAPI specification dictionary containing paths and servers.

        Returns:
            List of Namespace objects, each representing a detected API version
            or namespace. Returns empty list if no namespaces are detected.

        Example:
            >>> analyzer = NamespaceAnalyzer()
            >>> spec = {"paths": {"/v1/users": {}, "/v2/users": {}}}
            >>> namespaces = analyzer.detect_namespaces(spec)
            >>> [ns.name for ns in namespaces]
            ['v1', 'v2']
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
        """Extract namespace from an API path.

        Detects versioning patterns in API paths including:
        - Numeric versions (v1, v2, v3, etc.)
        - Environment tags (beta, alpha, canary, preview)
        - API prefix patterns (/api/v1)

        Args:
            path: API path string to analyze.

        Returns:
            Namespace name (e.g., "v1", "beta") if detected, or None if no
            namespace pattern is found.

        Example:
            >>> analyzer = NamespaceAnalyzer()
            >>> analyzer.extract_namespace_from_path("/api/v1/users")
            'v1'
            >>> analyzer.extract_namespace_from_path("/v2/products")
            'v2'
            >>> analyzer.extract_namespace_from_path("/beta/features")
            'beta'
            >>> analyzer.extract_namespace_from_path("/users")
            None
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
        """Extract namespace from a server URL.

        Parses a server URL to extract versioning information from the path
        component. Removes the protocol and domain, then analyzes the path
        using the same logic as extract_namespace_from_path.

        Args:
            url: Server URL string (e.g., "https://api.example.com/v1").

        Returns:
            Namespace name if detected in the URL path, or None if no
            namespace pattern is found.

        Example:
            >>> analyzer = NamespaceAnalyzer()
            >>> analyzer.extract_namespace_from_url("https://api.example.com/v1")
            'v1'
            >>> analyzer.extract_namespace_from_url("http://localhost:8000/api/beta")
            'beta'
            >>> analyzer.extract_namespace_from_url("https://api.example.com")
            None
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
        """Group paths by their detected namespace.

        Analyzes all paths in the specification and groups them by their
        namespace. Paths without a detected namespace are grouped under
        "default".

        Args:
            paths: OpenAPI paths dictionary containing all API paths.

        Returns:
            Dictionary mapping namespace names to lists of path strings.
            Paths without a namespace are grouped under "default".

        Example:
            >>> analyzer = NamespaceAnalyzer()
            >>> paths = {"/v1/users": {}, "/v1/products": {}, "/v2/users": {}}
            >>> grouped = analyzer.group_paths_by_namespace(paths)
            >>> print(grouped)
            {'v1': ['/v1/users', '/v1/products'], 'v2': ['/v2/users']}
        """
        grouped: dict[str, list[str]] = {}

        for path in paths:
            namespace = self.extract_namespace_from_path(path) or "default"
            if namespace not in grouped:
                grouped[namespace] = []
            grouped[namespace].append(path)

        return grouped
