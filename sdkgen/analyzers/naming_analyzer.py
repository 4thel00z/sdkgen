"""Naming convention analyzer for detecting API patterns."""

from dataclasses import dataclass
from typing import Any
from typing import Literal

from sdkgen.utils.case_converter import detect_naming_convention


@dataclass
class NamingAnalyzer:
    """Analyzes naming conventions in OpenAPI specifications.

    Detects and analyzes naming patterns used in API schemas, parameters,
    and responses. Helps determine the appropriate naming conventions for
    generated SDK code based on the API's conventions. Supports snake_case,
    camelCase, and original naming preservation.

    This analyzer is stateless and all methods can be called independently.
    """

    def detect_field_naming(
        self, schema: dict[str, Any]
    ) -> Literal["snake_case", "camelCase", "original"]:
        """Detect field naming convention from schema properties.

        Samples up to 10 field names from the schema properties and analyzes
        their naming conventions. Returns the dominant convention found.

        Args:
            schema: OpenAPI schema object with properties to analyze.

        Returns:
            Detected naming convention: "snake_case" if most fields use
            underscores, "camelCase" if most use camel case, or "original"
            if no clear pattern is detected or schema has no properties.

        Example:
            >>> analyzer = NamingAnalyzer()
            >>> schema = {"properties": {"first_name": {}, "last_name": {}}}
            >>> analyzer.detect_field_naming(schema)
            'snake_case'
            >>> schema = {"properties": {"firstName": {}, "lastName": {}}}
            >>> analyzer.detect_field_naming(schema)
            'camelCase'
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
        """Detect parameter naming convention.

        Samples up to 10 parameters and counts how many use snake_case
        versus camelCase conventions. Returns the dominant pattern.

        Args:
            parameters: List of OpenAPI parameter objects with "name" fields.

        Returns:
            Detected naming convention: "snake_case" if most parameters use
            underscores, "camelCase" if most use camel case, or "original"
            if no parameters or no clear pattern.

        Example:
            >>> analyzer = NamingAnalyzer()
            >>> params = [{"name": "user_id"}, {"name": "order_id"}]
            >>> analyzer.detect_parameter_naming(params)
            'snake_case'
            >>> params = [{"name": "userId"}, {"name": "orderId"}]
            >>> analyzer.detect_parameter_naming(params)
            'camelCase'
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
        """Determine if input models should use snake_case.

        For Python SDKs, this always returns True to follow Pythonic
        conventions. Input parameters should use snake_case regardless
        of the API's naming conventions for better Python code style.

        Args:
            spec: OpenAPI specification (currently unused, but kept for
                potential future use and API consistency).

        Returns:
            Always returns True to enforce Pythonic snake_case for inputs.

        Example:
            >>> analyzer = NamingAnalyzer()
            >>> analyzer.should_use_snake_case_for_input({})
            True
        """
        return True

    def should_use_api_naming_for_output(
        self, schema: dict[str, Any]
    ) -> Literal["snake_case", "camelCase", "original"]:
        """Determine naming convention for output models.

        Output models should match the API's actual naming convention
        to ensure proper serialization/deserialization. This delegates
        to detect_field_naming to determine the API's convention.

        Args:
            schema: OpenAPI schema object to analyze.

        Returns:
            Naming convention that matches the API: "snake_case",
            "camelCase", or "original".

        Example:
            >>> analyzer = NamingAnalyzer()
            >>> schema = {"properties": {"firstName": {}, "lastName": {}}}
            >>> analyzer.should_use_api_naming_for_output(schema)
            'camelCase'
        """
        return self.detect_field_naming(schema)

    def analyze_spec_examples(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Analyze OpenAPI specification to detect naming patterns.

        Performs comprehensive analysis of schemas and parameters throughout
        the specification to determine the dominant naming conventions used
        for requests, responses, and parameters.

        Args:
            spec: Complete OpenAPI specification dictionary.

        Returns:
            Dictionary with keys:
            - "request_naming": Always "snake_case" (Pythonic convention)
            - "response_naming": Detected from schemas ("snake_case", "camelCase", or "original")
            - "parameter_naming": Detected from parameters ("snake_case", "camelCase", or "original")

        Example:
            >>> analyzer = NamingAnalyzer()
            >>> spec = {
            ...     "components": {"schemas": {"User": {"properties": {"firstName": {}}}}},
            ...     "paths": {"/users": {"get": {"parameters": [{"name": "userId"}]}}}
            ... }
            >>> result = analyzer.analyze_spec_examples(spec)
            >>> print(result)
            {'request_naming': 'snake_case', 'response_naming': 'camelCase', 'parameter_naming': 'camelCase'}
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
