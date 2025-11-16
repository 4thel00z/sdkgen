"""Naming convention analyzer for detecting API patterns."""

from dataclasses import dataclass
from typing import Any
from typing import Literal

from sdkgen.utils.case_converter import detect_naming_convention


@dataclass
class NamingAnalyzer:
    """Analyzes naming conventions in OpenAPI specs."""

    def detect_field_naming(
        self, schema: dict[str, Any]
    ) -> Literal["snake_case", "camelCase", "original"]:
        """
        Detect field naming convention from schema properties.

        Args:
            schema: OpenAPI schema object

        Returns:
            Detected naming convention
        """
        properties = schema.get("properties", {})
        if not properties:
            return "original"

        # Sample field names
        field_names = list(properties.keys())[:10]

        # Count conventions
        counts = {"snake_case": 0, "camelCase": 0, "PascalCase": 0, "SCREAMING_SNAKE_CASE": 0}

        for name in field_names:
            convention = detect_naming_convention(name)
            if convention in counts:
                counts[convention] += 1

        # Determine dominant convention
        if counts["snake_case"] > counts["camelCase"]:
            return "snake_case"
        if counts["camelCase"] > 0:
            return "camelCase"

        return "original"

    def detect_parameter_naming(
        self, parameters: list[dict[str, Any]]
    ) -> Literal["snake_case", "camelCase", "original"]:
        """
        Detect parameter naming convention.

        Args:
            parameters: List of OpenAPI parameters

        Returns:
            Detected naming convention
        """
        if not parameters:
            return "original"

        param_names = [p.get("name", "") for p in parameters[:10]]

        snake_count = sum(1 for name in param_names if "_" in name)
        camel_count = sum(
            1 for name in param_names if any(c.isupper() for c in name) and "_" not in name
        )

        if snake_count > camel_count:
            return "snake_case"
        if camel_count > 0:
            return "camelCase"

        return "original"

    def should_use_snake_case_for_input(self, spec: dict[str, Any]) -> bool:
        """
        Determine if input models should use snake_case.

        For Python SDKs, we always prefer snake_case for inputs (Pythonic).

        Args:
            spec: OpenAPI specification

        Returns:
            True if input should use snake_case
        """
        return True

    def should_use_api_naming_for_output(
        self, schema: dict[str, Any]
    ) -> Literal["snake_case", "camelCase", "original"]:
        """
        Determine naming for output models (should match API).

        Args:
            schema: OpenAPI schema

        Returns:
            Naming convention for output models
        """
        return self.detect_field_naming(schema)

    def analyze_spec_examples(self, spec: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze examples in spec to detect patterns.

        Args:
            spec: OpenAPI specification

        Returns:
            Analysis results
        """
        results = {
            "request_naming": "snake_case",
            "response_naming": "camelCase",
            "parameter_naming": "camelCase",
        }

        # Analyze schemas
        schemas = spec.get("components", {}).get("schemas", {})
        if schemas:
            sample_schema: dict[str, Any] = next(iter(schemas.values()), {})
            response_naming = self.detect_field_naming(sample_schema)
            results["response_naming"] = response_naming

        # Analyze parameters
        paths = spec.get("paths", {})
        all_params = []
        for path_item in paths.values():
            for operation in path_item.values():
                if isinstance(operation, dict) and "parameters" in operation:
                    all_params.extend(operation["parameters"])

        if all_params:
            param_naming = self.detect_parameter_naming(all_params)
            results["parameter_naming"] = param_naming

        return results
