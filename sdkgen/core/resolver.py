"""Reference resolver for OpenAPI $ref resolution."""

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from sdkgen.utils.http_cache import HTTPCache


class ReferenceResolver:
    """Resolves $ref references in OpenAPI specifications."""

    def __init__(self, base_path: Path | None = None, cache: HTTPCache | None = None):
        """
        Initialize reference resolver.

        Args:
            base_path: Base path for resolving relative file references
            cache: HTTP cache for remote references
        """
        self.base_path = base_path or Path.cwd()
        self.cache = cache or HTTPCache()
        self.resolved_cache: dict[str, Any] = {}
        self.resolving: set[str] = set()

    async def resolve(self, spec: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve all $ref references in a spec.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Spec with all references resolved
        """
        self.resolved_cache = {}
        self.resolving = set()
        return await self.resolve_node(spec, spec)

    async def resolve_node(
        self, node: Any, root_spec: dict[str, Any], current_path: str = "#"
    ) -> Any:
        """
        Recursively resolve references in a node.

        Args:
            node: Current node to resolve
            root_spec: Root specification for local references
            current_path: Current JSON path in the spec

        Returns:
            Resolved node
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
        """
        Resolve a single $ref.

        Args:
            ref: Reference string (e.g., "#/components/schemas/Pet" or "external.yaml#/Pet")
            root_spec: Root specification for local references

        Returns:
            Resolved reference
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
        """
        Resolve a local reference within a spec.

        Args:
            path: JSON pointer path (e.g., "/components/schemas/Pet")
            spec: Specification to resolve within

        Returns:
            Resolved value
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
        """
        Load an external specification file.

        Args:
            file_ref: File path or URL

        Returns:
            Loaded specification
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
        """
        Extract all $ref values from a spec.

        Args:
            spec: OpenAPI specification

        Returns:
            List of unique $ref values
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
