"""OpenAPI specification parser with validation."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from sdkgen.core.resolver import ReferenceResolver
from sdkgen.utils.http_cache import HTTPCache


class OpenAPIParser:
    """Parser for OpenAPI specifications."""

    def __init__(self, cache: HTTPCache | None = None):
        """
        Initialize OpenAPI parser.

        Args:
            cache: HTTP cache for remote specs
        """
        self.cache = cache or HTTPCache()

    async def parse(self, source: str | Path, resolve_refs: bool = True) -> dict[str, Any]:
        """
        Parse an OpenAPI specification from file or URL.

        Args:
            source: File path or URL to OpenAPI spec
            resolve_refs: Whether to resolve $ref references

        Returns:
            Parsed OpenAPI specification
        """
        # Load the spec
        spec = await self.load_spec(source)

        # Validate basic structure
        self.validate_spec(spec)

        # Resolve references if requested
        if resolve_refs:
            base_path = self.get_base_path(source)
            resolver = ReferenceResolver(base_path=base_path, cache=self.cache)
            spec = await resolver.resolve(spec)

        return spec

    async def load_spec(self, source: str | Path) -> dict[str, Any]:
        """
        Load specification from file or URL.

        Args:
            source: File path or URL

        Returns:
            Loaded specification dictionary
        """
        source_str = str(source)

        # Check if URL
        parsed = urlparse(source_str)
        if parsed.scheme in ("http", "https"):
            return await self.load_from_url(source_str)

        # Local file
        return self.load_from_file(Path(source))

    async def load_from_url(self, url: str) -> dict[str, Any]:
        """
        Load spec from URL.

        Args:
            url: URL to fetch

        Returns:
            Loaded specification
        """
        return await self.cache.fetch(url)

    def load_from_file(self, path: Path) -> dict[str, Any]:
        """
        Load spec from local file.

        Args:
            path: Path to spec file

        Returns:
            Loaded specification
        """
        if not path.exists():
            msg = f"File not found: {path}"
            raise FileNotFoundError(msg)

        with path.open() as f:
            content = f.read()

            # Try JSON first
            if path.suffix == ".json":
                return json.loads(content)

            # Try YAML
            if path.suffix in (".yaml", ".yml"):
                return yaml.safe_load(content)

            # Auto-detect
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return yaml.safe_load(content)

    def validate_spec(self, spec: dict[str, Any]) -> None:
        """
        Validate OpenAPI spec structure.

        Args:
            spec: Specification to validate

        Raises:
            ValueError: If spec is invalid
        """
        # Check for required fields
        if "openapi" not in spec:
            msg = "Missing required field: openapi"
            raise ValueError(msg)

        # Validate version
        version = spec["openapi"]
        if not version.startswith("3."):
            msg = f"Unsupported OpenAPI version: {version}. Only 3.x is supported."
            raise ValueError(msg)

        # Check for info
        if "info" not in spec:
            msg = "Missing required field: info"
            raise ValueError(msg)

        info = spec["info"]
        if "title" not in info:
            msg = "Missing required field: info.title"
            raise ValueError(msg)

        if "version" not in info:
            msg = "Missing required field: info.version"
            raise ValueError(msg)

    def get_base_path(self, source: str | Path) -> Path:
        """
        Get base path for resolving relative references.

        Args:
            source: Original source path or URL

        Returns:
            Base path for resolution
        """
        source_str = str(source)

        # For URLs, use current directory
        parsed = urlparse(source_str)
        if parsed.scheme in ("http", "https"):
            return Path.cwd()

        # For files, use parent directory
        path = Path(source_str)
        if path.is_file():
            return path.parent
        return path

    def extract_metadata(self, spec: dict[str, Any]) -> dict[str, Any]:
        """
        Extract metadata from OpenAPI spec.

        Args:
            spec: OpenAPI specification

        Returns:
            Extracted metadata
        """
        info = spec.get("info", {})

        return {
            "title": info.get("title", ""),
            "version": info.get("version", ""),
            "description": info.get("description", ""),
            "license": info.get("license", {}).get("name"),
            "contact": info.get("contact", {}),
            "servers": spec.get("servers", []),
        }

    def get_base_url(self, spec: dict[str, Any]) -> str:
        """
        Extract base URL from servers.

        Args:
            spec: OpenAPI specification

        Returns:
            Base URL (first server or empty string)
        """
        servers = spec.get("servers", [])
        if servers and len(servers) > 0:
            return servers[0].get("url", "")
        return ""
