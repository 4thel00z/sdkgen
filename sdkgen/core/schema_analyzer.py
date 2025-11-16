"""Schema analyzer for handling OpenAPI schema compositions."""

from dataclasses import dataclass
from typing import Any
from typing import Literal

from sdkgen.core.ir import Composition
from sdkgen.core.ir import Discriminator


@dataclass
class SchemaAnalyzer:
    """Analyzes OpenAPI schemas for compositions and patterns."""

    def analyze_composition(self, schema: dict[str, Any]) -> Composition | None:
        """
        Analyze schema for allOf/oneOf/anyOf compositions.

        Args:
            schema: OpenAPI schema object

        Returns:
            Composition object or None if not a composition
        """
        if "allOf" in schema:
            return self.build_composition("allOf", schema["allOf"], schema)

        if "oneOf" in schema:
            return self.build_composition("oneOf", schema["oneOf"], schema)

        if "anyOf" in schema:
            return self.build_composition("anyOf", schema["anyOf"], schema)

        return None

    def build_composition(
        self,
        comp_type: Literal["allOf", "oneOf", "anyOf"],
        schemas: list[dict[str, Any]],
        parent_schema: dict[str, Any],
    ) -> Composition:
        """
        Build composition from schemas.

        Args:
            comp_type: Type of composition (allOf, oneOf, anyOf)
            schemas: List of schemas to compose
            parent_schema: Parent schema containing discriminator info

        Returns:
            Composition object
        """
        # Extract discriminator if present
        discriminator = (
            self.extract_discriminator(parent_schema["discriminator"])
            if "discriminator" in parent_schema
            else None
        )

        # Extract schema references
        schema_refs = []
        for schema in schemas:
            if "$ref" in schema:
                ref_path = schema["$ref"]
                ref_name = ref_path.split("/")[-1]
                schema_refs.append(ref_name)
            else:
                # Inline schema - would need to create anonymous model
                schema_refs.append(schema)

        return Composition(type=comp_type, schemas=schema_refs, discriminator=discriminator)

    def extract_discriminator(self, disc_schema: dict[str, Any]) -> Discriminator:
        """
        Extract discriminator information.

        Args:
            disc_schema: Discriminator schema from OpenAPI

        Returns:
            Discriminator object
        """
        property_name = disc_schema.get("propertyName", "type")
        mapping = disc_schema.get("mapping", {})

        return Discriminator(property_name=property_name, mapping=mapping)

    def merge_all_of_schemas(self, schemas: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Merge allOf schemas into single schema.

        Args:
            schemas: List of schemas to merge

        Returns:
            Merged schema
        """
        merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

        for schema in schemas:
            # Merge properties
            if "properties" in schema:
                merged["properties"].update(schema["properties"])

            # Merge required
            if "required" in schema:
                merged["required"].extend(schema["required"])

            # Merge other fields
            for key in ("description", "title"):
                if key in schema and key not in merged:
                    merged[key] = schema[key]

        # Remove duplicates from required
        merged["required"] = list(set(merged["required"]))

        return merged

    def is_composition(self, schema: dict[str, Any]) -> bool:
        """
        Check if schema is a composition.

        Args:
            schema: OpenAPI schema

        Returns:
            True if composition
        """
        return any(k in schema for k in ("allOf", "oneOf", "anyOf"))

    def get_composition_type(self, schema: dict[str, Any]) -> str | None:
        """
        Get composition type from schema.

        Args:
            schema: OpenAPI schema

        Returns:
            Composition type or None
        """
        for comp_type in ("allOf", "oneOf", "anyOf"):
            if comp_type in schema:
                return comp_type
        return None
