"""Endpoint analyzer for grouping operations into resources."""

from dataclasses import dataclass
from typing import Any

from sdkgen.utils.name_sanitizer import sanitize_class_name


@dataclass
class EndpointAnalyzer:
    """Analyzes endpoints and groups them into resources."""

    def group_by_tags(
        self, spec: dict[str, Any]
    ) -> dict[str, list[tuple[str, str, dict[str, Any]]]]:
        """
        Group operations by tags.

        Args:
            spec: OpenAPI specification

        Returns:
            Dictionary mapping tag to list of (path, method, operation) tuples
        """
        grouped: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}

        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            for method in ("get", "post", "put", "patch", "delete", "head", "options"):
                if method not in path_item:
                    continue

                operation = path_item[method]
                tags = operation.get("tags", [])

                if not tags:
                    # Use path-based grouping
                    tags = [self.extract_resource_from_path(path)]

                for tag in tags:
                    if tag not in grouped:
                        grouped[tag] = []
                    grouped[tag].append((path, method.upper(), operation))

        return grouped

    def extract_resource_from_path(self, path: str) -> str:
        """
        Extract resource name from path.

        Examples:
            /users/{id} -> users
            /api/v1/products -> products

        Args:
            path: API path

        Returns:
            Resource name
        """
        parts = path.strip("/").split("/")

        # Filter out version/api prefixes and path parameters
        resource_parts = [
            p
            for p in parts
            if (not p.startswith("{") and not p.startswith("v"))
            or (not p[1:].isdigit() and p not in ("api", "beta", "alpha"))
        ]

        if resource_parts:
            return resource_parts[0]

        return "default"

    def create_resource_name(self, tag: str) -> str:
        """
        Create resource class name from tag.

        Args:
            tag: OpenAPI tag

        Returns:
            PascalCase resource name
        """
        # Clean and convert to PascalCase
        name = sanitize_class_name(tag)

        # Pluralize if not already
        if not name.endswith("s") and not name.endswith("S"):
            name = f"{name}s"

        return name

    def detect_path_prefix(self, paths: list[str]) -> str | None:
        """
        Detect common path prefix for a resource.

        Args:
            paths: List of paths

        Returns:
            Common prefix or None
        """
        if not paths:
            return None

        if len(paths) == 1:
            # Extract base path (without parameters)
            path = paths[0]
            parts = path.strip("/").split("/")
            # Remove parameters
            base_parts = [p for p in parts if not p.startswith("{")]
            if base_parts:
                return "/" + "/".join(base_parts[:2])
            return None

        # Find common prefix
        common_prefix = None
        for path in paths:
            parts = path.strip("/").split("/")
            base_parts = [p for p in parts if not p.startswith("{")]

            if not base_parts:
                continue

            prefix = "/" + base_parts[0]
            if common_prefix is None:
                common_prefix = prefix
            elif not common_prefix.startswith(prefix) and not prefix.startswith(common_prefix):
                # Different prefixes
                return None

        return common_prefix

    def requires_resource_id(self, paths: list[str]) -> tuple[bool, str | None]:
        """
        Determine if resource requires ID in constructor.

        Args:
            paths: List of paths for this resource

        Returns:
            Tuple of (requires_id, param_name)
        """
        # Check if all paths have a common ID parameter
        id_params = set()

        for path in paths:
            parts = path.strip("/").split("/")
            for part in parts:
                if part.startswith("{") and part.endswith("}"):
                    param = part[1:-1]
                    if "id" in param.lower():
                        id_params.add(param)

        # If all paths share an ID parameter, resource needs it
        if len(id_params) == 1:
            param_name = id_params.pop()
            return True, param_name

        return False, None

    def response_is_array(self, responses: dict[str, Any]) -> bool:
        """Check if primary response is an array."""
        for status in ["200", "201"]:
            response = responses.get(status)
            if not response:
                continue
            schema = response.get("content", {}).get("application/json", {}).get("schema")
            if schema:
                return schema.get("type") == "array"
        return False

    def clean_operation_id(self, operation_id: str) -> str:
        """Extract method name from operationId (FastAPI pattern)."""
        if "_api_" in operation_id:
            parts = operation_id.split("_api_")[0].split("_")
            if parts and parts[-1] in ("v1", "v2", "beta"):
                parts = parts[:-1]
            return "_".join(parts)
        return operation_id

    def infer_operation_name(
        self, method: str, path: str, operation_id: str | None, responses: dict[str, Any]
    ) -> str:
        """
        Infer operation method name using 3-priority system.

        Priority 1: Clean operationId
        Priority 2: RPC-style actions (sub-resource actions)
        Priority 3: HTTP method + response schema

        Args:
            method: HTTP method
            path: API path
            operation_id: Operation ID from spec
            responses: Response schemas

        Returns:
            Method name in snake_case
        """
        # Extract path parts (excluding params)
        path_parts = [p for p in path.strip("/").split("/") if not p.startswith("{")]
        has_path_param = "{" in path

        # PRIORITY 1: Clean operationId
        if operation_id:
            cleaned = self.clean_operation_id(operation_id)
            # If cleaned operationId is a simple verb, use it
            if cleaned in (
                "create",
                "list",
                "get",
                "update",
                "delete",
                "download",
                "upload",
                "export",
                "import",
            ):
                return cleaned

        # PRIORITY 2: RPC-style actions (expanded ACTION_WORDS)
        if len(path_parts) > 1:
            last_part = path_parts[-1]
            action_words = {
                # File operations
                "download",
                "upload",
                "export",
                "import",
                # State changes
                "activate",
                "deactivate",
                "enable",
                "disable",
                "publish",
                "unpublish",
                "archive",
                "unarchive",
                # Workflow
                "approve",
                "reject",
                "cancel",
                "complete",
                "submit",
                "confirm",
                "verify",
                "validate",
                # Execution
                "execute",
                "trigger",
                "run",
                "start",
                "stop",
                "pause",
                "resume",
                "retry",
                "restart",
                # Data operations
                "refresh",
                "sync",
                "clone",
                "duplicate",
                "copy",
                "resend",
                "reprocess",
                # Utility
                "summary",
                "status",
                "health",
                "me",
                "current",
            }
            if last_part in action_words:
                return last_part.lower()

        # PRIORITY 3: HTTP method + response schema
        if method == "GET":
            if not has_path_param:
                # GET without params: check if array response
                if self.response_is_array(responses):
                    return "list"
                # Otherwise, use path-based name for utility endpoints
                if path_parts:
                    return path_parts[-1].lower()
                return "get"
            else:
                # GET with params: always use get
                return "get"
        elif method == "POST":
            return "create"
        elif method in ("PUT", "PATCH"):
            return "update"
        elif method == "DELETE":
            return "delete"

        # Fallback
        return method.lower()
