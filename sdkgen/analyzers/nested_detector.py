"""Nested resource pattern detector."""

from dataclasses import dataclass
from typing import Any


@dataclass
class NestedDetector:
    """Detects nested resource patterns from operation IDs and paths.

    Analyzes API operations to identify nested resource patterns where
    operations are logically grouped under a parent resource. Supports
    detection via custom extensions (x-nested-resource) and operation ID
    patterns. Helps organize generated SDK code with proper resource hierarchy.

    This analyzer is stateless and all methods can be called independently.
    """

    def detect_nested_resources(
        self, operations: list[tuple[str, str, dict[str, Any]]]
    ) -> dict[str, list[tuple[str, str, dict[str, Any]]]]:
        """Detect nested resources from a list of operations.

        Analyzes operations to identify nested resource patterns using two
        detection methods:
        1. Custom x-nested-resource extension in operation objects
        2. Operation ID patterns like "resource_nested_action"

        Args:
            operations: List of tuples, each containing (path, HTTP_method,
                operation_dict).

        Returns:
            Dictionary mapping nested resource names to lists of their
            operations. Each operation list contains (path, method, operation)
            tuples.

        Example:
            >>> detector = NestedDetector()
            >>> ops = [
            ...     ("/stages/{id}/instruct", "POST", {"operationId": "stages_instruct_create"}),
            ...     ("/stages/{id}/instruct/{iid}", "GET", {"operationId": "stages_instruct_get"})
            ... ]
            >>> nested = detector.detect_nested_resources(ops)
            >>> print(nested.keys())
            dict_keys(['instruct'])
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
        """Extract nested resource name from operation ID.

        Parses operation IDs to identify nested resource patterns while
        avoiding false positives from FastAPI auto-generated IDs and
        operation IDs that start with action verbs.

        Pattern detection:
        - Expects format: resource_nested_action (minimum 3 parts)
        - Returns the second part as the nested resource name
        - Ignores if first part is an action verb
        - Ignores FastAPI patterns (long IDs with "api" segment)

        Args:
            operation_id: Operation ID string from OpenAPI specification.

        Returns:
            Nested resource name (second segment) if pattern is detected,
            or None if not a nested resource pattern.

        Example:
            >>> detector = NestedDetector()
            >>> detector.extract_nested_from_operation_id("stages_instruct_create")
            'instruct'
            >>> detector.extract_nested_from_operation_id("users_admin_list")
            'admin'
            >>> detector.extract_nested_from_operation_id("upload_file_v1_api")
            None
            >>> detector.extract_nested_from_operation_id("get_user")
            None
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
        """Get property name for nested resource accessor.

        Converts a nested resource name to a lowercase property name suitable
        for use as a Python attribute accessor in the generated SDK.

        Args:
            nested_name: Nested resource name extracted from operation ID or
                custom extension.

        Returns:
            Lowercase property name for accessing the nested resource.

        Example:
            >>> detector = NestedDetector()
            >>> detector.get_nested_property_name("Instruct")
            'instruct'
            >>> detector.get_nested_property_name("ADMIN")
            'admin'
        """
        return nested_name.lower()

    def should_create_nested_resource(
        self, operations_count: int, pattern_confidence: float = 0.5
    ) -> bool:
        """Determine if a nested resource should be created.

        Evaluates whether a detected nested pattern has sufficient operations
        to warrant creating a separate nested resource class in the generated
        SDK. This prevents creating unnecessary classes for single-operation
        patterns.

        Args:
            operations_count: Number of operations detected in the nested group.
            pattern_confidence: Confidence threshold for pattern detection.
                Currently unused but reserved for future heuristics.
                Defaults to 0.5.

        Returns:
            True if a nested resource class should be generated, False if
            operations should be kept in the parent resource.

        Example:
            >>> detector = NestedDetector()
            >>> detector.should_create_nested_resource(3)
            True
            >>> detector.should_create_nested_resource(1)
            False
        """
        # Create nested resource if we have at least 2 operations
        return operations_count >= 2
