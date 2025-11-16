"""Type mapper for converting OpenAPI types to IR types."""

from typing import Any

from sdkgen.core.ir import IRType
from sdkgen.core.ir import ValidationRules


class TypeMapper:
    """Maps OpenAPI schema types to IR types."""

    def map_schema(self, schema: dict[str, Any]) -> IRType:
        """
        Map an OpenAPI schema to an IR type.

        Args:
            schema: OpenAPI schema object

        Returns:
            IR type representation
        """
        # Handle empty schema
        if not schema:
            return IRType(kind="any")

        # Handle $ref (should be resolved already, but just in case)
        if "$ref" in schema:
            ref_path = schema["$ref"]
            ref_name = ref_path.split("/")[-1]
            return IRType(kind="model_ref", ref_name=ref_name)

        # Handle nullable
        nullable = schema.get("nullable", False)

        # Handle anyOf/oneOf - create union
        if "oneOf" in schema or "anyOf" in schema:
            union_schemas = schema.get("oneOf") or schema.get("anyOf", [])
            union_types = [self.map_schema(s) for s in union_schemas]
            return IRType(kind="union", union_types=union_types, nullable=nullable)

        # Handle type
        schema_type = schema.get("type")

        # No type specified
        if schema_type is None:
            if any(k in schema for k in ("allOf", "oneOf", "anyOf")):
                return IRType(kind="any", nullable=nullable)
            return IRType(kind="any", nullable=nullable)

        # Array type
        if schema_type == "array":
            items = schema.get("items", {})
            item_type = self.map_schema(items) if items else IRType(kind="any")
            return IRType(kind="array", item_type=item_type, nullable=nullable)

        # Object type
        if schema_type == "object":
            # Additional properties or inline object
            return IRType(kind="object", nullable=nullable)

        # Enum type
        if "enum" in schema:
            enum_values = schema["enum"]
            # Create literal type for small enums
            if len(enum_values) <= 5:
                return IRType(kind="literal", literal_value=enum_values, nullable=nullable)
            return IRType(kind="enum_ref", nullable=nullable)

        # Primitive types
        if schema_type in ("string", "integer", "number", "boolean"):
            # Handle binary format for file uploads
            if schema_type == "string" and schema.get("format") == "binary":
                return IRType(kind="primitive", primitive="bytes", nullable=nullable)
            return IRType(kind="primitive", primitive=schema_type, nullable=nullable)

        # Unknown type
        return IRType(kind="any", nullable=nullable)

    def extract_validation_rules(self, schema: dict[str, Any]) -> ValidationRules | None:
        """
        Extract validation rules from schema.

        Args:
            schema: OpenAPI schema object

        Returns:
            Validation rules or None
        """
        rules: dict[str, Any] = {}

        # Numeric constraints
        if "minimum" in schema:
            rules["min"] = schema["minimum"]
        if "maximum" in schema:
            rules["max"] = schema["maximum"]

        # String constraints
        if "minLength" in schema:
            rules["min_length"] = schema["minLength"]
        if "maxLength" in schema:
            rules["max_length"] = schema["maxLength"]
        if "pattern" in schema:
            rules["pattern"] = schema["pattern"]
        if "format" in schema:
            rules["format"] = schema["format"]

        if not rules:
            return None

        return ValidationRules(**rules)

    def is_enum(self, schema: dict[str, Any]) -> bool:
        """
        Check if schema represents an enum.

        Args:
            schema: OpenAPI schema

        Returns:
            True if enum
        """
        return "enum" in schema

    def is_array(self, schema: dict[str, Any]) -> bool:
        """
        Check if schema represents an array.

        Args:
            schema: OpenAPI schema

        Returns:
            True if array
        """
        return schema.get("type") == "array"

    def is_object(self, schema: dict[str, Any]) -> bool:
        """
        Check if schema represents an object.

        Args:
            schema: OpenAPI schema

        Returns:
            True if object
        """
        return schema.get("type") == "object"

    def is_primitive(self, schema: dict[str, Any]) -> bool:
        """
        Check if schema represents a primitive type.

        Args:
            schema: OpenAPI schema

        Returns:
            True if primitive
        """
        return schema.get("type") in ("string", "integer", "number", "boolean")

    def get_python_type_hint(self, ir_type: IRType) -> str:
        """
        Get Python type hint string from IR type.

        Args:
            ir_type: IR type

        Returns:
            Python type hint as string
        """
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "bytes": "bytes",
        }

        if ir_type.kind == "primitive":
            base = type_map.get(ir_type.primitive, "Any")
        elif ir_type.kind == "array":
            item_hint = self.get_python_type_hint(ir_type.item_type) if ir_type.item_type else "Any"
            base = f"list[{item_hint}]"
        elif ir_type.kind == "model_ref":
            base = ir_type.ref_name  # Don't quote - with __future__ annotations it's fine
        elif ir_type.kind == "enum_ref":
            base = ir_type.ref_name
        elif ir_type.kind == "literal":
            # Literal values
            if isinstance(ir_type.literal_value, list):
                values = [f'"{v}"' if isinstance(v, str) else str(v) for v in ir_type.literal_value]
                base = f"Literal[{', '.join(values)}]"
            else:
                base = "Any"
        elif ir_type.kind == "union":
            if ir_type.union_types:
                types = [self.get_python_type_hint(t) for t in ir_type.union_types]
                base = " | ".join(types)
            else:
                base = "Any"
        elif ir_type.kind == "object":
            base = "dict[str, Any]"
        else:
            base = "Any"

        return f"{base} | None" if ir_type.nullable else base
