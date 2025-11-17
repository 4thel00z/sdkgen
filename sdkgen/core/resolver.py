"""Reference resolver for OpenAPI $ref resolution."""

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from sdkgen.utils.http_cache import HTTPCache


class ReferenceResolver:
    """Resolves $ref references in OpenAPI specifications.

    Handles resolution of both local references (#/components/schemas/Pet)
    and external references (external.yaml#/Pet or URLs). Supports circular
    reference detection and caching to prevent infinite loops and redundant
    resolution.

    Attributes:
        base_path: Base directory for resolving relative file references.
        cache: HTTPCache instance for fetching remote references.
        resolved_cache: Cache of already resolved references.
        resolving: Set of references currently being resolved (for cycle detection).
    """

    def __init__(self, base_path: Path | None = None, cache: HTTPCache | None = None):
        """Initialize reference resolver with base path and cache.

        Args:
            base_path: Base path for resolving relative file references.
                If None, uses current working directory. Defaults to None.
            cache: HTTP cache instance for remote references. If None,
                creates new HTTPCache instance. Defaults to None.

        Example:
            >>> resolver = ReferenceResolver()  # Uses cwd
            >>> resolver = ReferenceResolver(base_path=Path("/specs"))
        """
        self.base_path = base_path or Path.cwd()
        self.cache = cache or HTTPCache()
        self.resolved_cache: dict[str, Any] = {}
        self.resolving: set[str] = set()

    async def resolve(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Resolve all $ref references in a specification.

        Recursively traverses the entire specification and resolves all
        $ref references, whether local or external. Resets caches before
        resolution to ensure clean state.

        Args:
            spec: OpenAPI specification dictionary with potential $ref references.

        Returns:
            New specification dictionary with all $ref references replaced
            by their actual content. Circular references are replaced with
            {"$circular_ref": "<ref>"} markers.

        Example:
            >>> resolver = ReferenceResolver()
            >>> spec = {"components": {"schemas": {"Pet": {"$ref": "#/components/schemas/Animal"}}}}
            >>> resolved = await resolver.resolve(spec)
        """
        self.resolved_cache = {}
        self.resolving = set()
        return await self.resolve_node(spec, spec)

    async def resolve_node(
        self, node: Any, root_spec: dict[str, Any], current_path: str = "#"
    ) -> Any:
        """Recursively resolve references in a node.

        Traverses a node and its children, resolving any $ref references
        encountered. Handles circular reference detection and caching.

        Args:
            node: Current node to resolve. Can be dict, list, or primitive value.
            root_spec: Root specification dictionary for resolving local references.
            current_path: Current JSON pointer path in the spec (for debugging).
                Defaults to "#" (root).

        Returns:
            Resolved node with same structure as input but with $ref references
            replaced. Circular references are marked with {"$circular_ref": "<ref>"}.

        Example:
            >>> resolver = ReferenceResolver()
            >>> node = {"$ref": "#/components/schemas/Pet"}
            >>> resolved = await resolver.resolve_node(node, spec)
        """
        if isinstance(node, dict):
            # Handle $ref
            if "$ref" in node:
                ref = node["$ref"]

                # Detect circular reference
                if ref in self.resolving:
                    return {"$circular_ref": ref}

                # Check cache
                if ref in self.resolved_cache:
                    return self.resolved_cache[ref]

                # Mark as resolving
                self.resolving.add(ref)

                try:
                    resolved = await self.resolve_reference(ref, root_spec)
                    self.resolved_cache[ref] = resolved
                    return resolved
                finally:
                    self.resolving.discard(ref)

            # Recursively resolve nested objects
            result = {}
            for key, value in node.items():
                result[key] = await self.resolve_node(value, root_spec, f"{current_path}/{key}")
            return result

        if isinstance(node, list):
            # Recursively resolve list items
            return [
                await self.resolve_node(item, root_spec, f"{current_path}[{i}]")
                for i, item in enumerate(node)
            ]

        return node

    async def resolve_reference(self, ref: str, root_spec: dict[str, Any]) -> Any:
        """Resolve a single $ref reference.

        Handles both local references (starting with #) and external references
        (file paths or URLs, optionally with # anchors).

        Args:
            ref: Reference string. Examples:
                - "#/components/schemas/Pet" (local reference)
                - "external.yaml#/Pet" (external file with anchor)
                - "https://example.com/spec.json#/schemas/User" (URL with anchor)
            root_spec: Root specification dictionary for local references.

        Returns:
            Resolved content from the reference location.

        Raises:
            FileNotFoundError: If external file doesn't exist.
            ValueError: If reference path is invalid.

        Example:
            >>> resolver = ReferenceResolver()
            >>> resolved = await resolver.resolve_reference("#/components/schemas/Pet", spec)
        """
        # Parse reference
        if "#" in ref:
            file_part, path_part = ref.split("#", 1)
        else:
            file_part = ref
            path_part = ""

        # Local reference
        if not file_part:
            return self.resolve_local_reference(path_part, root_spec)

        # External reference
        external_spec = await self.load_external_spec(file_part)

        if not path_part:
            return external_spec

        return self.resolve_local_reference(path_part, external_spec)

    def resolve_local_reference(self, path: str, spec: dict[str, Any]) -> Any:
        """Resolve a local reference within a specification.

        Uses JSON Pointer syntax (RFC 6901) to navigate to a specific
        location within the specification. Handles special character
        escaping (~0 for ~, ~1 for /).

        Args:
            path: JSON pointer path (e.g., "/components/schemas/Pet").
                Leading slash is optional. Empty or "/" returns root.
            spec: Specification dictionary to resolve within.

        Returns:
            Value at the referenced location.

        Raises:
            ValueError: If the path is invalid or doesn't exist.
            KeyError: If a referenced key doesn't exist.
            IndexError: If a referenced array index is out of bounds.

        Example:
            >>> resolver = ReferenceResolver()
            >>> spec = {"components": {"schemas": {"Pet": {"type": "object"}}}}
            >>> resolver.resolve_local_reference("/components/schemas/Pet", spec)
            {'type': 'object'}
        """
        if not path or path == "/":
            return spec

        # Remove leading /
        if path.startswith("/"):
            path = path[1:]

        # Navigate path
        parts = path.split("/")
        current = spec

        for part in parts:
            # Unescape JSON pointer special characters
            unescaped_part = part.replace("~1", "/").replace("~0", "~")

            if isinstance(current, dict):
                current = current[unescaped_part]
            elif isinstance(current, list):
                current = current[int(unescaped_part)]
            else:
                msg = f"Invalid reference path: {path}"
                raise ValueError(msg)

        return current

    async def load_external_spec(self, file_ref: str) -> dict[str, Any]:
        """Load an external specification file.

        Handles both remote URLs (via HTTP cache) and local files (relative
        or absolute paths). Local files are resolved relative to base_path.

        Args:
            file_ref: File path (relative or absolute) or URL (http/https).

        Returns:
            Loaded and parsed specification dictionary from the external source.

        Raises:
            FileNotFoundError: If local file doesn't exist.
            httpx.HTTPError: If URL fetch fails.
            yaml.YAMLError: If file parsing fails.

        Example:
            >>> resolver = ReferenceResolver(base_path=Path("/specs"))
            >>> spec = await resolver.load_external_spec("common.yaml")
            >>> spec = await resolver.load_external_spec("https://example.com/spec.json")
        """
        # Check if it's a URL
        parsed = urlparse(file_ref)
        if parsed.scheme in ("http", "https"):
            return await self.cache.fetch(file_ref)

        # Local file
        file_path = Path(file_ref) if Path(file_ref).is_absolute() else self.base_path / file_ref

        if not file_path.exists():
            msg = f"External spec not found: {file_path}"
            raise FileNotFoundError(msg)

        with file_path.open() as f:
            if file_path.suffix in (".yaml", ".yml"):
                return yaml.safe_load(f)
            return yaml.safe_load(f)

    def extract_schema_refs(self, spec: dict[str, Any]) -> list[str]:
        """Extract all $ref values from a specification.

        Recursively traverses the entire specification and collects all
        $ref reference strings. Returns unique references only.

        Args:
            spec: OpenAPI specification dictionary to scan for references.

        Returns:
            List of unique $ref strings found in the specification.
            Order is not guaranteed.

        Example:
            >>> resolver = ReferenceResolver()
            >>> spec = {
            ...     "components": {"schemas": {"Pet": {"$ref": "#/components/schemas/Animal"}}},
            ...     "paths": {"/pets": {"get": {"responses": {"200": {"$ref": "#/components/responses/PetList"}}}}}
            ... }
            >>> refs = resolver.extract_schema_refs(spec)
            >>> print(refs)
            ['#/components/schemas/Animal', '#/components/responses/PetList']
        """
        refs: list[str] = []

        def visit(node: Any) -> None:
            if isinstance(node, dict):
                if "$ref" in node:
                    refs.append(node["$ref"])
                for value in node.values():
                    visit(value)
            elif isinstance(node, list):
                for item in node:
                    visit(item)

        visit(spec)
        return list(set(refs))
