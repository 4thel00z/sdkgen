"""IR Builder - orchestrates parsing and building complete IR from OpenAPI spec."""

import re
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Literal
from typing import cast

from sdkgen.analyzers.endpoint_analyzer import EndpointAnalyzer
from sdkgen.analyzers.namespace_analyzer import NamespaceAnalyzer
from sdkgen.analyzers.naming_analyzer import NamingAnalyzer
from sdkgen.analyzers.nested_detector import NestedDetector
from sdkgen.core.ir import AuthConfig
from sdkgen.core.ir import AuthScheme
from sdkgen.core.ir import ClientConfig
from sdkgen.core.ir import ClientProperty
from sdkgen.core.ir import Converter
from sdkgen.core.ir import Enum
from sdkgen.core.ir import EnumValue
from sdkgen.core.ir import EnvVar
from sdkgen.core.ir import FieldConversion
from sdkgen.core.ir import IRType
from sdkgen.core.ir import Model
from sdkgen.core.ir import NestedResource
from sdkgen.core.ir import Operation
from sdkgen.core.ir import Parameter
from sdkgen.core.ir import PathParam
from sdkgen.core.ir import ProjectMetadata
from sdkgen.core.ir import Property
from sdkgen.core.ir import Resource
from sdkgen.core.ir import SDKProject
from sdkgen.core.ir import TypeRegistry
from sdkgen.core.ir import UtilityConfig
from sdkgen.core.ir import UtilityMethod
from sdkgen.core.schema_analyzer import SchemaAnalyzer
from sdkgen.core.type_mapper import TypeMapper
from sdkgen.utils.case_converter import to_snake_case
from sdkgen.utils.name_sanitizer import sanitize_class_name
from sdkgen.utils.name_sanitizer import sanitize_enum_member_name
from sdkgen.utils.name_sanitizer import sanitize_package_name


@dataclass
class IRBuilder:
    """Builds IR from parsed OpenAPI specification."""

    endpoint_analyzer: EndpointAnalyzer = field(default_factory=EndpointAnalyzer)
    namespace_analyzer: NamespaceAnalyzer = field(default_factory=NamespaceAnalyzer)
    naming_analyzer: NamingAnalyzer = field(default_factory=NamingAnalyzer)
    nested_detector: NestedDetector = field(default_factory=NestedDetector)
    schema_analyzer: SchemaAnalyzer = field(default_factory=SchemaAnalyzer)
    type_mapper: TypeMapper = field(default_factory=TypeMapper)

    def build(self, spec: dict[str, Any], package_name: str | None = None) -> SDKProject:
        """
        Build complete IR from OpenAPI spec.

        Args:
            spec: Parsed and resolved OpenAPI specification
            package_name: Override package name (default: from spec title)

        Returns:
            Complete SDK project IR
        """
        # Extract metadata
        metadata = self.build_metadata(spec, package_name)

        # Build authentication config
        auth = self.build_auth_config(spec)

        # Detect namespaces
        namespaces = self.namespace_analyzer.detect_namespaces(spec)

        # Build type registry
        types = self.build_type_registry(spec)

        # Build client config
        client = self.build_client_config(spec, auth)

        # Build resources
        resources = self.build_resources(spec, namespaces)

        # Build utilities
        utilities = self.build_utilities(types)

        return SDKProject(
            metadata=metadata,
            auth=auth,
            namespaces=namespaces,
            types=types,
            client=client,
            resources=resources,
            utilities=utilities,
        )

    def build_metadata(
        self, spec: dict[str, Any], package_name: str | None = None
    ) -> ProjectMetadata:
        """Build project metadata from spec."""
        info = spec.get("info", {})

        title = info.get("title", "SDK")
        name = sanitize_package_name(package_name) if package_name else sanitize_package_name(title)

        # Get base URL from servers
        servers = spec.get("servers", [])
        base_url = servers[0].get("url", "") if servers else ""

        return ProjectMetadata(
            name=name,
            version=info.get("version", "0.1.0"),
            description=info.get("description", ""),
            license=info.get("license", {}).get("name") if "license" in info else None,
            author=info.get("contact", {}).get("name") if "contact" in info else None,
            base_url=base_url,
        )

    def build_auth_config(self, spec: dict[str, Any]) -> AuthConfig:
        """Build authentication configuration."""
        security_schemes = spec.get("components", {}).get("securitySchemes", {})
        schemes: list[AuthScheme] = []

        for name, scheme_spec in security_schemes.items():
            scheme = AuthScheme(
                name=name,
                type=scheme_spec.get("type", "http"),
                scheme=scheme_spec.get("scheme"),
                in_location=scheme_spec.get("in"),
                parameter_name=scheme_spec.get("name"),
                env_var_name=f"{name.upper()}_API_KEY"
                if scheme_spec.get("type") == "apiKey"
                else f"{name.upper()}_TOKEN",
                header_name=scheme_spec.get("name")
                if scheme_spec.get("in") == "header"
                else "Authorization",
            )
            schemes.append(scheme)

        # Determine default scheme
        default = schemes[0].name if schemes else None

        return AuthConfig(schemes=schemes, default=default)

    def build_type_registry(self, spec: dict[str, Any]) -> TypeRegistry:
        """Build type registry with all models and enums."""
        schemas = spec.get("components", {}).get("schemas", {})

        models: list[Model] = []
        enums: list[Enum] = []

        for schema_name, schema in schemas.items():
            # Check if enum
            if "enum" in schema:
                enum = self.build_enum(schema_name, schema)
                enums.append(enum)
            else:
                model = self.build_model(schema_name, schema)
                models.append(model)

        return TypeRegistry(models=models, enums=enums, type_aliases=[])

    def build_model(self, name: str, schema: dict[str, Any]) -> Model:
        """Build a model from schema."""
        # Detect if input or output model
        # For now, use naming convention detection
        field_naming = self.naming_analyzer.detect_field_naming(schema)

        # Extract properties
        properties: list[Property] = []
        required = schema.get("required", [])

        for prop_name, prop_schema in schema.get("properties", {}).items():
            prop = self.build_property(prop_name, prop_schema, field_naming, prop_name in required)
            properties.append(prop)

        # Check for composition
        composition = self.schema_analyzer.analyze_composition(schema)

        return Model(
            name=sanitize_class_name(name),
            type="composed" if composition else "object",
            field_naming=field_naming,
            description=schema.get("description"),
            properties=properties,
            required=required,
            composition=composition,
            is_input=name.endswith("Input") or name.endswith("Request"),
            is_output=name.endswith("Response")
            or name.endswith("Output")
            or not name.endswith("Input"),
        )

    def build_property(
        self, name: str, schema: dict[str, Any], field_naming: str, required: bool
    ) -> Property:
        """Build a property from schema."""
        python_name = to_snake_case(name)
        api_name = name  # Keep original for API

        ir_type = self.type_mapper.map_schema(schema)
        validation = self.type_mapper.extract_validation_rules(schema)

        return Property(
            name=name,
            python_name=python_name,
            api_name=api_name,
            type=ir_type,
            description=schema.get("description"),
            required=required,
            nullable=schema.get("nullable", False),
            validation=validation,
        )

    def build_enum(self, name: str, schema: dict[str, Any]) -> Enum:
        """Build an enum from schema."""
        enum_values = schema.get("enum", [])
        base_type: Literal["string", "integer"] = (
            "string" if isinstance(enum_values[0], str) else "integer"
        )

        values: list[EnumValue] = []
        for value in enum_values:
            enum_name = sanitize_enum_member_name(str(value))
            values.append(EnumValue(name=enum_name, value=value))

        return Enum(
            name=sanitize_class_name(name),
            base_type=base_type,
            description=schema.get("description"),
            values=values,
        )

    def build_client_config(self, spec: dict[str, Any], auth: AuthConfig) -> ClientConfig:
        """Build client configuration."""
        # Standard client parameters
        init_params = [
            Parameter(
                name="base_url",
                python_name="base_url",
                api_name="base_url",
                location="query",
                type=IRType(kind="primitive", primitive="string"),
                required=False,
                default="",
            ),
            Parameter(
                name="api_key",
                python_name="api_key",
                api_name="api_key",
                location="query",
                type=IRType(kind="primitive", primitive="string"),
                required=False,
                default="",
            ),
        ]

        # Environment variables
        env_vars = [
            EnvVar(name="BASE_URL", maps_to="base_url", required=True),
            EnvVar(name="API_KEY", maps_to="api_key", required=True),
        ]

        # Properties
        properties = [
            ClientProperty(
                name="timeout", type=IRType(kind="primitive", primitive="number"), default=600.0
            ),
            ClientProperty(name="headers", type=IRType(kind="object"), default={}),
        ]

        # Utility methods
        utility_methods = [
            UtilityMethod(
                name="with_options",
                description="Create a new client with updated options",
                template="copy_with_overrides",
            ),
            UtilityMethod(
                name="with_namespace",
                description="Create a new client with base_url + namespace",
                template="copy_with_path_prefix",
            ),
        ]

        return ClientConfig(
            name="Client",
            init_params=init_params,
            env_vars=env_vars,
            properties=properties,
            methods=["request", "request_raw"],
            utility_methods=utility_methods,
        )

    def build_resources(self, spec: dict[str, Any], namespaces: list) -> list[Resource]:
        """Build resources from endpoints."""
        # Group operations by tags
        grouped = self.endpoint_analyzer.group_by_tags(spec)

        resources: list[Resource] = []

        for tag, operations in grouped.items():
            resource_name = self.endpoint_analyzer.create_resource_name(tag)

            # Extract paths
            paths = [op[0] for op in operations]
            path_prefix = self.endpoint_analyzer.detect_path_prefix(paths)
            requires_id, id_param = self.endpoint_analyzer.requires_resource_id(paths)

            # Determine namespace from paths
            resource_namespace = self.determine_resource_namespace(paths, namespaces)

            # Build operations
            resource_operations = []
            for path, method, operation_spec in operations:
                operation = self.build_operation(path, method, operation_spec)
                resource_operations.append(operation)

            # Detect nested resources
            nested_groups = self.nested_detector.detect_nested_resources(operations)
            nested_resources: list[NestedResource] = []
            nested_paths_methods = set()

            for nested_ops in nested_groups.values():
                if self.nested_detector.should_create_nested_resource(len(nested_ops)):
                    # Build nested resource operations
                    nested_operations = []
                    for path, method, operation_spec in nested_ops:
                        operation = self.build_operation(path, method, operation_spec)
                        nested_operations.append(operation)
                        nested_paths_methods.add((path, method))

                    # Remove from main operations by matching path+method
                    resource_operations = [
                        op
                        for op in resource_operations
                        if (op.path, op.method) not in nested_paths_methods
                    ]

            resources.append(
                Resource(
                    name=resource_name,
                    namespace=resource_namespace,
                    tag=tag,
                    path_prefix=path_prefix,
                    operations=resource_operations,
                    nested_resources=nested_resources,
                    requires_id=requires_id,
                    id_param_name=id_param,
                )
            )

        return resources

    def determine_resource_namespace(self, paths: list[str], namespaces: list) -> str | None:
        """Determine which namespace a resource belongs to based on its paths."""
        if not paths or not namespaces:
            return None

        # Check first path to determine namespace
        first_path = paths[0]

        for namespace in namespaces:
            if namespace.path_prefix in first_path:
                return namespace.name

        # Default to first namespace if paths don't match any
        return namespaces[0].name if namespaces else None

    def build_operation(self, path: str, method: str, spec: dict[str, Any]) -> Operation:
        """Build an operation from OpenAPI operation spec."""
        operation_id = spec.get("operationId")
        responses = spec.get("responses", {})
        operation_name = self.endpoint_analyzer.infer_operation_name(
            method, path, operation_id, responses
        )

        # Extract path parameters
        path_params = self.extract_path_params(path, spec.get("parameters", []))

        # Extract query parameters
        query_params = self.extract_query_params(spec.get("parameters", []))

        # Extract request body and determine format
        request_body_spec = spec.get("requestBody")
        body_params = self.extract_request_body_params(request_body_spec)
        return_format = self.determine_request_format(request_body_spec)

        # Determine if should use unpack pattern (model ref in body)
        use_unpack = self.should_use_unpack(request_body_spec)

        # Extract response type
        responses = spec.get("responses", {})
        response_type = self.extract_response_type(responses)

        # Clean description
        description = self.clean_html(spec.get("description") or spec.get("summary") or "")

        return Operation(
            name=operation_name,
            operation_id=operation_id,
            method=cast(
                "Literal['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS']",
                method.upper(),
            ),
            path=path,
            path_params=path_params,
            query_params=query_params,
            body_params=body_params,
            description=description,
            summary=spec.get("summary"),
            response_type=response_type,
            return_format=cast(
                "Literal['json', 'binary', 'text', 'stream', 'multipart']", return_format
            ),
            use_unpack_pattern=use_unpack,
            tags=spec.get("tags", []),
            deprecated=spec.get("deprecated", False),
            is_async=True,
        )

    def extract_path_params(self, path: str, parameters: list[dict[str, Any]]) -> list:
        """Extract path parameters from path template and parameter list."""
        # Find all {param} in path
        param_names = re.findall(r"\{([^}]+)\}", path)

        return [
            PathParam(
                name=param_name,
                python_name=to_snake_case(param_name),
                type=self.extract_path_param_type(param_name, parameters),
                description=self.get_param_description(param_name, parameters),
            )
            for param_name in param_names
        ]

    def extract_path_param_type(self, param_name: str, parameters: list[dict[str, Any]]) -> IRType:
        """Extract type for path parameter."""
        param_spec = next(
            (p for p in parameters if p.get("in") == "path" and p.get("name") == param_name), None
        )

        if param_spec and "schema" in param_spec:
            return self.type_mapper.map_schema(param_spec["schema"])

        # Default to string
        return IRType(kind="primitive", primitive="string")

    def get_param_description(
        self, param_name: str, parameters: list[dict[str, Any]]
    ) -> str | None:
        """Get description for parameter."""
        param_spec = next((p for p in parameters if p.get("name") == param_name), None)
        return param_spec.get("description") if param_spec else None

    def extract_query_params(self, parameters: list[dict[str, Any]]) -> list:
        """Extract query parameters from parameter list."""
        return [
            Parameter(
                name=param_spec.get("name", ""),
                python_name=to_snake_case(param_spec.get("name", "")),
                api_name=param_spec.get("name", ""),
                location="query",
                type=self.type_mapper.map_schema(param_spec.get("schema", {})),
                description=param_spec.get("description"),
                required=param_spec.get("required", False),
                default=param_spec.get("schema", {}).get("default"),
            )
            for param_spec in parameters
            if param_spec.get("in") == "query"
        ]

    def extract_response_type(self, responses: dict[str, Any]) -> IRType | None:
        """Extract return type from responses."""
        # Try success responses in order
        for status in ["200", "201", "202"]:
            response = responses.get(status)
            if not response:
                continue

            content = response.get("content", {})

            # Try JSON content
            json_schema = content.get("application/json", {}).get("schema")
            if json_schema:
                return self.type_mapper.map_schema(json_schema)

            # Try other content types
            for content_spec in content.values():
                if "schema" in content_spec:
                    return self.type_mapper.map_schema(content_spec["schema"])

        # Try default response
        default_response = responses.get("default")
        if default_response:
            content = default_response.get("content", {})
            json_schema = content.get("application/json", {}).get("schema")
            if json_schema:
                return self.type_mapper.map_schema(json_schema)

        # 204 No Content
        if "204" in responses:
            return None

        # Fallback: assume dict for 200/201 responses without explicit schema
        if "200" in responses or "201" in responses:
            return IRType(kind="object")

        return None

    def extract_request_body_params(self, request_body: dict[str, Any] | None) -> list:
        """Extract parameters from request body schema."""
        if not request_body:
            return []

        content = request_body.get("content", {})

        # Try all content types
        schema = (
            content.get("application/json", {}).get("schema")
            or content.get("multipart/form-data", {}).get("schema")
            or content.get("application/x-www-form-urlencoded", {}).get("schema")
        )

        if not schema:
            return []

        # Case 1: Model reference -> use Unpack pattern (handled elsewhere)
        if "$ref" in schema:
            return []

        # Case 2: Array type -> create single param with array type
        if schema.get("type") == "array":
            items_schema = schema.get("items", {})
            param_name = self.infer_array_param_name(items_schema)

            return [
                Parameter(
                    name=param_name,
                    python_name=to_snake_case(param_name),
                    api_name=param_name,
                    location="body",
                    type=IRType(kind="array", item_type=self.type_mapper.map_schema(items_schema)),
                    required=True,
                )
            ]

        # Case 3: Object with properties -> extract each property as param
        if schema.get("type") == "object" and "properties" in schema:
            properties = schema["properties"]
            required = schema.get("required", [])

            return [
                Parameter(
                    name=prop_name,
                    python_name=to_snake_case(prop_name),
                    api_name=prop_name,
                    location="body",
                    type=self.extract_property_type(prop_schema),
                    description=prop_schema.get("description"),
                    required=prop_name in required,
                )
                for prop_name, prop_schema in properties.items()
            ]

        return []

    def infer_array_param_name(self, items_schema: dict[str, Any]) -> str:
        """Infer parameter name for array body based on items type."""
        if "$ref" in items_schema:
            ref_name = items_schema["$ref"].split("/")[-1]
            # CreateUserRequest -> users
            base_name = ref_name.replace("Request", "").replace("Create", "").replace("Update", "")
            return (
                base_name.lower() + "s"
                if not base_name.lower().endswith("s")
                else base_name.lower()
            )
        return "items"

    def extract_property_type(self, prop_schema: dict[str, Any]) -> IRType:
        """Extract type for property, handling binary format."""
        # Handle binary file uploads
        if prop_schema.get("type") == "string" and prop_schema.get("format") == "binary":
            return IRType(kind="primitive", primitive="bytes")

        return self.type_mapper.map_schema(prop_schema)

    def determine_request_format(self, request_body: dict[str, Any] | None) -> str:
        """Determine request content type."""
        if not request_body:
            return "json"

        content = request_body.get("content", {})

        if "multipart/form-data" in content:
            return "multipart"
        if "application/x-www-form-urlencoded" in content:
            return "urlencoded"

        return "json"

    def should_use_unpack(self, request_body: dict[str, Any] | None) -> bool:
        """Determine if should use Unpack pattern."""
        if not request_body:
            return False

        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema")

        # Use unpack if body is a model reference
        return bool(schema and "$ref" in schema)

    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""

        # Remove HTML tags
        cleaned = re.sub(r"<[^>]+>", "", text)
        # Remove excessive whitespace
        cleaned = " ".join(cleaned.split())
        # Limit length
        return cleaned[:500]

    def build_utilities(self, types: TypeRegistry) -> UtilityConfig:
        """Build utility functions (converters, helpers)."""
        converters: list[Converter] = []

        # Create converters for input models
        for model in types.models:
            if model.is_input:
                converter = self.build_converter(model)
                converters.append(converter)

        return UtilityConfig(converters=converters, helpers=[])

    def build_converter(self, model: Model) -> Converter:
        """Build converter function for a model."""
        converter_name = f"{to_snake_case(model.name)}_to_api"

        conversions: list[FieldConversion] = []
        for prop in model.properties:
            # Convert snake_case to camelCase
            conversion = FieldConversion(
                from_name=prop.python_name,
                to_name=prop.api_name,
                conditional_omit=not prop.required,
                nested_convert=prop.type.kind == "model_ref",
            )
            conversions.append(conversion)

        return Converter(
            name=converter_name, input_type=model.name, output_type="dict", conversions=conversions
        )
