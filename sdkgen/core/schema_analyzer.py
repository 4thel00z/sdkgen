"""Schema analyzer for handling OpenAPI schema compositions."""

from dataclasses import dataclass
from typing import Any
from typing import Literal

from sdkgen.core.ir import Composition
from sdkgen.core.ir import Discriminator


@dataclass
class SchemaAnalyzer:
    """Analyzes OpenAPI schemas for compositions and patterns.

    Handles analysis of schema compositions (allOf, oneOf, anyOf), discriminators,
    and schema merging. Helps process complex schema patterns for SDK generation.

    This analyzer is stateless and all methods can be called independently.
    """

    def analyze_composition(self, schema: dict[str, Any]) -> Composition | None:
        """Analyze schema for composition patterns.

        Detects and analyzes allOf, oneOf, or anyOf compositions in OpenAPI
        schemas. Returns composition metadata including discriminator information
        if present.

        Args:
            schema: OpenAPI schema object dictionary to analyze.

        Returns:
            Composition object if schema contains allOf, oneOf, or anyOf,
            None otherwise.

        Example:
            >>> analyzer = SchemaAnalyzer()
            >>> schema = {"oneOf": [{"$ref": "#/components/schemas/Cat"}, {"$ref": "#/components/schemas/Dog"}]}
            >>> comp = analyzer.analyze_composition(schema)
            >>> print(comp.type)
            'oneOf'
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
        """Build composition object from schema list.

        Constructs a Composition object by extracting schema references
        and discriminator information. Handles both ref-based schemas
        and inline schemas.

        Args:
            comp_type: Type of composition - "allOf", "oneOf", or "anyOf".
            schemas: List of schema objects to compose.
            parent_schema: Parent schema dictionary that may contain
                discriminator information.

        Returns:
            Composition object with type, schema references, and optional
            discriminator.

        Example:
            >>> analyzer = SchemaAnalyzer()
            >>> schemas = [{"$ref": "#/components/schemas/Cat"}]
            >>> comp = analyzer.build_composition("oneOf", schemas, {})
            >>> print(comp.schemas)
            ['Cat']
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
        """Extract discriminator information from schema.

        Parses OpenAPI discriminator object to extract the property name
        used for type discrimination and optional mapping of values to
        schema names.

        Args:
            disc_schema: Discriminator object from OpenAPI schema.

        Returns:
            Discriminator object with property name and optional mapping.

        Example:
            >>> analyzer = SchemaAnalyzer()
            >>> disc = {"propertyName": "petType", "mapping": {"dog": "#/components/schemas/Dog"}}
            >>> result = analyzer.extract_discriminator(disc)
            >>> print(result.property_name)
            'petType'
        """
        property_name = disc_schema.get("propertyName", "type")
        mapping = disc_schema.get("mapping", {})

        return Discriminator(property_name=property_name, mapping=mapping)

    def merge_all_of_schemas(self, schemas: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge allOf schemas into a single combined schema.

        Combines multiple schemas by merging properties, required fields,
        and metadata. Used for flattening allOf compositions into a single
        schema definition.

        Args:
            schemas: List of schema objects to merge together.

        Returns:
            Merged schema dictionary with combined properties, required
            fields, and metadata from all input schemas.

        Example:
            >>> analyzer = SchemaAnalyzer()
            >>> schemas = [
            ...     {"properties": {"name": {"type": "string"}}, "required": ["name"]},
            ...     {"properties": {"age": {"type": "integer"}}}
            ... ]
            >>> merged = analyzer.merge_all_of_schemas(schemas)
            >>> print(list(merged["properties"].keys()))
            ['name', 'age']
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
        """Check if schema is a composition.

        Determines whether a schema uses any composition keywords
        (allOf, oneOf, anyOf).

        Args:
            schema: OpenAPI schema object to check.

        Returns:
            True if schema contains allOf, oneOf, or anyOf, False otherwise.

        Example:
            >>> analyzer = SchemaAnalyzer()
            >>> analyzer.is_composition({"allOf": []})
            True
            >>> analyzer.is_composition({"type": "object"})
            False
        """
        return any(k in schema for k in ("allOf", "oneOf", "anyOf"))

    def get_composition_type(self, schema: dict[str, Any]) -> str | None:
        """Get composition type from schema.

        Identifies which composition keyword is used in the schema.

        Args:
            schema: OpenAPI schema object to analyze.

        Returns:
            Composition type string ("allOf", "oneOf", or "anyOf") if found,
            None if schema is not a composition.

        Example:
            >>> analyzer = SchemaAnalyzer()
            >>> analyzer.get_composition_type({"oneOf": []})
            'oneOf'
            >>> analyzer.get_composition_type({"type": "string"})
            None
        """
        for comp_type in ("allOf", "oneOf", "anyOf"):
            if comp_type in schema:
                return comp_type
        return None
