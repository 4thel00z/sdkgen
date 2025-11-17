"""OpenAPI specification parser with validation."""

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from sdkgen.core.resolver import ReferenceResolver
from sdkgen.utils.http_cache import HTTPCache


class OpenAPIParser:
    """Parser for OpenAPI specifications.

    Handles loading, parsing, and validation of OpenAPI 3.x specifications
    from local files or remote URLs. Supports JSON and YAML formats with
    automatic detection. Optionally resolves $ref references.

    Attributes:
        cache: HTTPCache instance for caching remote specifications.
    """

    def __init__(self, cache: HTTPCache | None = None):
        """Initialize OpenAPI parser with optional cache.

        Args:
            cache: HTTP cache instance for caching remote specs. If None,
                creates a new HTTPCache instance with default settings.

        Example:
            >>> parser = OpenAPIParser()  # Default cache
            >>> custom_cache = HTTPCache(Path("/tmp/cache"))
            >>> parser = OpenAPIParser(cache=custom_cache)  # Custom cache
        """
        self.cache = cache or HTTPCache()

    async def parse(self, source: str | Path, resolve_refs: bool = True) -> dict[str, Any]:
        """Parse an OpenAPI specification from file or URL.

        Main entry point for parsing specifications. Handles loading, validation,
        and optional reference resolution in a single call.

        Args:
            source: File path (Path or string) or URL (string) to OpenAPI spec.
                Supports .json, .yaml, and .yml file extensions.
            resolve_refs: Whether to resolve all $ref references in the spec.
                Defaults to True.

        Returns:
            Fully parsed and optionally resolved OpenAPI specification dictionary.

        Raises:
            FileNotFoundError: If source is a local file that doesn't exist.
            ValueError: If spec is invalid or unsupported OpenAPI version.
            httpx.HTTPError: If URL fetch fails.

        Example:
            >>> parser = OpenAPIParser()
            >>> spec = await parser.parse("openapi.yaml")
            >>> spec = await parser.parse("https://api.example.com/openapi.json")
            >>> spec = await parser.parse("spec.yaml", resolve_refs=False)
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
        """Load specification from file or URL.

        Determines whether the source is a URL or local file and delegates
        to the appropriate loading method.

        Args:
            source: File path (Path or string) or URL (string) to load from.

        Returns:
            Loaded specification dictionary (not yet validated).

        Example:
            >>> parser = OpenAPIParser()
            >>> spec = await parser.load_spec("openapi.yaml")
            >>> spec = await parser.load_spec("https://example.com/spec.json")
        """
        source_str = str(source)

        # Check if URL
        parsed = urlparse(source_str)
        if parsed.scheme in ("http", "https"):
            return await self.load_from_url(source_str)

        # Local file
        return self.load_from_file(Path(source))

    async def load_from_url(self, url: str) -> dict[str, Any]:
        """Load spec from a remote URL.

        Uses the HTTP cache to fetch and cache the specification.

        Args:
            url: HTTP(S) URL to fetch the specification from.

        Returns:
            Loaded and parsed specification dictionary.

        Raises:
            httpx.HTTPError: If the request fails.

        Example:
            >>> parser = OpenAPIParser()
            >>> spec = await parser.load_from_url("https://api.example.com/openapi.json")
        """
        return await self.cache.fetch(url)

    def load_from_file(self, path: Path) -> dict[str, Any]:
        """Load spec from a local file.

        Supports JSON and YAML formats with automatic format detection
        based on file extension or content.

        Args:
            path: Path to the specification file.

        Returns:
            Loaded and parsed specification dictionary.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            json.JSONDecodeError: If JSON parsing fails.
            yaml.YAMLError: If YAML parsing fails.

        Example:
            >>> parser = OpenAPIParser()
            >>> spec = parser.load_from_file(Path("openapi.yaml"))
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
        """Validate OpenAPI specification structure.

        Performs basic validation checking for required fields and supported
        OpenAPI versions. Only validates structure, not semantic correctness.

        Args:
            spec: Specification dictionary to validate.

        Raises:
            ValueError: If spec is missing required fields or has unsupported
                OpenAPI version (only 3.x is supported).

        Example:
            >>> parser = OpenAPIParser()
            >>> spec = {"openapi": "3.0.0", "info": {"title": "API", "version": "1.0"}}
            >>> parser.validate_spec(spec)  # No exception
            >>> bad_spec = {"openapi": "2.0"}
            >>> parser.validate_spec(bad_spec)  # Raises ValueError
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
        """Get base path for resolving relative references.

        Determines the base directory for resolving $ref references to other
        files. For URLs, uses current working directory. For files, uses the
        parent directory.

        Args:
            source: Original source path (Path or string) or URL (string).

        Returns:
            Base path to use for resolving relative file references.

        Example:
            >>> parser = OpenAPIParser()
            >>> parser.get_base_path("/path/to/openapi.yaml")
            PosixPath('/path/to')
            >>> parser.get_base_path("https://example.com/spec.json")
            PosixPath('/current/working/directory')
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
        """Extract metadata from OpenAPI specification.

        Extracts common metadata fields like title, version, description,
        license, contact information, and server URLs.

        Args:
            spec: OpenAPI specification dictionary.

        Returns:
            Dictionary containing extracted metadata with keys: title, version,
            description, license, contact, servers.

        Example:
            >>> parser = OpenAPIParser()
            >>> spec = {"info": {"title": "My API", "version": "1.0", "description": "API docs"}}
            >>> metadata = parser.extract_metadata(spec)
            >>> print(metadata["title"])
            'My API'
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
        """Extract base URL from server definitions.

        Returns the URL of the first server in the servers array,
        which is typically used as the base URL for API requests.

        Args:
            spec: OpenAPI specification dictionary.

        Returns:
            Base URL string from the first server, or empty string if
            no servers are defined.

        Example:
            >>> parser = OpenAPIParser()
            >>> spec = {"servers": [{"url": "https://api.example.com/v1"}]}
            >>> parser.get_base_url(spec)
            'https://api.example.com/v1'
            >>> parser.get_base_url({})
            ''
        """
        servers = spec.get("servers", [])
        if servers and len(servers) > 0:
            return servers[0].get("url", "")
        return ""
