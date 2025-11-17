"""Endpoint analyzer for grouping operations into resources."""

from dataclasses import dataclass
from typing import Any


@dataclass
class EndpointAnalyzer:
    """Analyzes endpoints and groups them into resources.

    Provides functionality to analyze OpenAPI specification endpoints and
    organize them into logical resource groupings. Handles tag-based grouping,
    path analysis, resource extraction, and operation naming using a 3-priority
    system (operationId, RPC-style actions, HTTP method + response schema).

    This analyzer is stateless and all methods can be called independently.
    """

    def group_by_tags(
        self, spec: dict[str, Any]
    ) -> dict[str, list[tuple[str, str, dict[str, Any]]]]:
        """Group operations by OpenAPI tags.

        Organizes all operations in the specification by their tags. If an
        operation has no tags, it uses path-based resource extraction as a
        fallback. This enables resource-based SDK generation.

        Args:
            spec: OpenAPI specification dictionary containing paths and operations.

        Returns:
            Dictionary mapping each tag name to a list of tuples. Each tuple
            contains (path, HTTP_METHOD, operation_dict). The HTTP method is
            normalized to uppercase.

        Example:
            >>> analyzer = EndpointAnalyzer()
            >>> spec = {"paths": {"/users": {"get": {"tags": ["users"]}}}}
            >>> result = analyzer.group_by_tags(spec)
            >>> print(result)
            {'users': [('/users', 'GET', {...})]}
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
        """Extract resource name from an API path.

        Analyzes the path and extracts the primary resource name by filtering
        out version prefixes (v1, v2), API keywords, and path parameters. Uses
        the first significant path segment as the resource name.

        Args:
            path: API path string. Can include path parameters in {braces}.

        Returns:
            Resource name extracted from the path. Returns "default" if no
            valid resource name can be determined.

        Example:
            >>> analyzer = EndpointAnalyzer()
            >>> analyzer.extract_resource_from_path("/users/{id}")
            'users'
            >>> analyzer.extract_resource_from_path("/api/v1/products")
            'products'
            >>> analyzer.extract_resource_from_path("/v2/orders/{order_id}/items")
            'orders'
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

    def detect_path_prefix(self, paths: list[str]) -> str | None:
        """Detect common path prefix for a resource.

        Analyzes a list of paths to find a common prefix that all paths share.
        Filters out path parameters when determining the prefix.

        Args:
            paths: List of API path strings to analyze.

        Returns:
            Common prefix string starting with "/" if found, or None if no
            common prefix exists or paths list is empty.

        Example:
            >>> analyzer = EndpointAnalyzer()
            >>> paths = ["/api/users", "/api/users/{id}", "/api/products"]
            >>> analyzer.detect_path_prefix(paths)
            '/api'
            >>> paths = ["/users", "/products"]
            >>> analyzer.detect_path_prefix(paths)
            None
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
        """Determine if resource requires ID in constructor.

        Analyzes paths to detect if all paths share a common ID parameter,
        indicating the resource should be initialized with an ID.

        Args:
            paths: List of API path strings for a resource.

        Returns:
            Tuple of (requires_id, param_name) where:
            - requires_id: True if all paths share a common ID parameter
            - param_name: The name of the ID parameter (without braces),
              or None if no common ID exists

        Example:
            >>> analyzer = EndpointAnalyzer()
            >>> paths = ["/users/{user_id}", "/users/{user_id}/posts"]
            >>> analyzer.requires_resource_id(paths)
            (True, 'user_id')
            >>> paths = ["/users", "/products"]
            >>> analyzer.requires_resource_id(paths)
            (False, None)
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
        """Check if the primary response schema is an array.

        Examines 200 and 201 response schemas to determine if the response
        is an array type. Used in operation naming to distinguish list
        operations from single resource operations.

        Args:
            responses: OpenAPI responses dictionary from an operation.

        Returns:
            True if the primary response (200 or 201) has an array schema,
            False otherwise.

        Example:
            >>> analyzer = EndpointAnalyzer()
            >>> responses = {"200": {"content": {"application/json": {"schema": {"type": "array"}}}}}
            >>> analyzer.response_is_array(responses)
            True
        """
        for status in ["200", "201"]:
            response = responses.get(status)
            if not response:
                continue
            schema = response.get("content", {}).get("application/json", {}).get("schema")
            if schema:
                return schema.get("type") == "array"
        return False

    def clean_operation_id(self, operation_id: str) -> str:
        """Extract method name from operationId (FastAPI pattern).

        Cleans up operation IDs generated by FastAPI and similar frameworks
        by removing API and version suffixes (e.g., _api_v1_users_post).

        Args:
            operation_id: Original operation ID from OpenAPI specification.

        Returns:
            Cleaned operation ID with FastAPI patterns removed.

        Example:
            >>> analyzer = EndpointAnalyzer()
            >>> analyzer.clean_operation_id("create_user_api_v1_users_post")
            'create_user'
            >>> analyzer.clean_operation_id("list_items_api_beta")
            'list_items'
        """
        if "_api_" in operation_id:
            parts = operation_id.split("_api_")[0].split("_")
            if parts and parts[-1] in ("v1", "v2", "beta"):
                parts = parts[:-1]
            return "_".join(parts)
        return operation_id

    def infer_operation_name(
        self, method: str, path: str, operation_id: str | None, responses: dict[str, Any]
    ) -> str:
        """Infer operation method name using 3-priority system.

        Determines the best method name for an API operation using a
        three-tiered priority system:

        Priority 1: Clean operationId - Uses cleaned operation ID if it's
            a simple action verb (create, list, get, update, delete, etc.)

        Priority 2: RPC-style actions - Detects sub-resource action endpoints
            like /resource/{id}/download, using the action word (35+ supported)

        Priority 3: HTTP method + response schema - Falls back to semantic
            naming based on HTTP method and response type:
            - GET + array → list()
            - GET + object + param → get()
            - GET + object + no param → path-based name (health, status, etc.)
            - POST → create()
            - PUT/PATCH → update()
            - DELETE → delete()

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, etc.).
            path: API path string, may include path parameters.
            operation_id: Optional operation ID from OpenAPI specification.
            responses: OpenAPI responses dictionary for the operation.

        Returns:
            Method name in snake_case, suitable for use as a Python method name.

        Example:
            >>> analyzer = EndpointAnalyzer()
            >>> # Priority 1: operationId
            >>> analyzer.infer_operation_name("POST", "/users", "create", {})
            'create'
            >>> # Priority 2: RPC action
            >>> analyzer.infer_operation_name("GET", "/files/{id}/download", None, {})
            'download'
            >>> # Priority 3: HTTP method + response
            >>> responses = {"200": {"content": {"application/json": {"schema": {"type": "array"}}}}}
            >>> analyzer.infer_operation_name("GET", "/users", None, responses)
            'list'
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
