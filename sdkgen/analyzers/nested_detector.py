"""Nested resource pattern detector."""

from dataclasses import dataclass
from typing import Any


@dataclass
class NestedDetector:
    """Detects nested resource patterns from operation IDs and paths."""

    def detect_nested_resources(
        self, operations: list[tuple[str, str, dict[str, Any]]]
    ) -> dict[str, list[tuple[str, str, dict[str, Any]]]]:
        """
        Detect nested resources from operations.

        Looks for patterns like:
        - operationId: "stages_instruct_create"
        - x-nested-resource extension

        Args:
            operations: List of (path, method, operation) tuples

        Returns:
            Dictionary mapping nested resource name to operations
        """
        nested: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}

        for path, method, operation in operations:
            # Check for x-nested-resource extension
            if "x-nested-resource" in operation:
                nested_name = operation["x-nested-resource"]
                if nested_name not in nested:
                    nested[nested_name] = []
                nested[nested_name].append((path, method, operation))
                continue

            # Check operation ID pattern
            operation_id = operation.get("operationId", "")
            if not operation_id:
                continue

            nested_name = self.extract_nested_from_operation_id(operation_id)
            if not nested_name:
                continue

            if nested_name not in nested:
                nested[nested_name] = []
            nested[nested_name].append((path, method, operation))

        return nested

    def extract_nested_from_operation_id(self, operation_id: str) -> str | None:
        """
        Extract nested resource name from operation ID.

        Examples:
            stages_instruct_create -> instruct
            users_admin_list -> admin

        AVOID FALSE POSITIVES like:
            upload_file_v1_api... -> NOT nested (action verb at start)
            get_user_v1_api... -> NOT nested (action verb at start)

        Args:
            operation_id: Operation ID

        Returns:
            Nested resource name or None
        """
        parts = operation_id.split("_")

        # Ignore FastAPI auto-generated IDs (they have verbs at start and _api_ in them)
        if len(parts) > 5 and "api" in parts:
            return None

        # Ignore if first part is an action verb
        action_verbs = {
            "get",
            "list",
            "create",
            "update",
            "delete",
            "patch",
            "post",
            "put",
            "upload",
            "download",
            "fetch",
            "search",
            "find",
        }
        if parts[0].lower() in action_verbs:
            return None

        # Pattern: resource_nested_action (at least 3 parts, no verbs at start)
        if len(parts) >= 3:
            return parts[1]

        return None

    def get_nested_property_name(self, nested_name: str) -> str:
        """
        Get property name for nested resource accessor.

        Args:
            nested_name: Nested resource name

        Returns:
            Property name (lowercase)
        """
        return nested_name.lower()

    def should_create_nested_resource(
        self, operations_count: int, pattern_confidence: float = 0.5
    ) -> bool:
        """
        Determine if we should create a nested resource.

        Args:
            operations_count: Number of operations in nested group
            pattern_confidence: Confidence threshold

        Returns:
            True if should create nested resource
        """
        # Create nested resource if we have at least 2 operations
        return operations_count >= 2
