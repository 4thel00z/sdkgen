"""Intermediate Representation (IR) dataclass definitions for SDK generation."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Literal


@dataclass
class ProjectMetadata:
    """Metadata about the SDK project."""

    name: str
    version: str
    description: str
    license: str | None = None
    author: str | None = None
    base_url: str = ""


@dataclass
class AuthScheme:
    """Authentication scheme configuration."""

    name: str
    type: Literal["http", "apiKey", "oauth2", "openIdConnect"]
    scheme: str | None = None
    in_location: str | None = None
    parameter_name: str | None = None
    env_var_name: str = ""
    header_name: str | None = None


@dataclass
class AuthConfig:
    """Authentication configuration for the SDK."""

    schemes: list[AuthScheme] = field(default_factory=list)
    default: str | None = None


@dataclass
class Namespace:
    """API namespace (e.g., v1, beta)."""

    name: str
    path_prefix: str
    description: str | None = None
    resources: list[str] = field(default_factory=list)
    deprecated: bool = False


@dataclass
class ValidationRules:
    """Validation rules for properties."""

    min: int | float | None = None
    max: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    format: str | None = None


@dataclass
class IRType:
    """Type representation in IR."""

    kind: Literal[
        "primitive", "array", "object", "model_ref", "enum_ref", "union", "any", "literal"
    ]
    primitive: Literal["string", "integer", "number", "boolean", "bytes"] | None = None
    item_type: IRType | None = None
    properties: list[Property] | None = None
    ref_name: str | None = None
    union_types: list[IRType] | None = None
    literal_value: Any | None = None
    nullable: bool = False


@dataclass
class Property:
    """Property definition for models."""

    name: str
    python_name: str
    api_name: str
    type: IRType
    description: str | None = None
    required: bool = False
    nullable: bool = False
    deprecated: bool = False
    default: Any | None = None
    examples: list[Any] = field(default_factory=list)
    validation: ValidationRules | None = None


@dataclass
class Discriminator:
    """Discriminator for polymorphic types."""

    property_name: str
    mapping: dict[str, str] = field(default_factory=dict)


@dataclass
class Composition:
    """Schema composition (allOf, oneOf, anyOf)."""

    type: Literal["allOf", "oneOf", "anyOf"]
    schemas: list[str | Model] = field(default_factory=list)
    discriminator: Discriminator | None = None


@dataclass
class Model:
    """Data model definition."""

    name: str
    type: Literal["object", "composed"]
    field_naming: Literal["snake_case", "camelCase", "original"]
    description: str | None = None
    properties: list[Property] = field(default_factory=list)
    required: list[str] = field(default_factory=list)
    additional_properties: bool | IRType = False
    composition: Composition | None = None
    is_input: bool = False
    is_output: bool = False
    is_nested: bool = False
    original_ref: str | None = None
    examples: list[dict] = field(default_factory=list)


@dataclass
class EnumValue:
    """Enum value definition."""

    name: str
    value: str | int
    description: str | None = None
    deprecated: bool = False


@dataclass
class Enum:
    """Enum type definition."""

    name: str
    base_type: Literal["string", "integer"]
    description: str | None = None
    values: list[EnumValue] = field(default_factory=list)


@dataclass
class TypeAlias:
    """Type alias definition."""

    name: str
    target_type: IRType
    description: str | None = None


@dataclass
class TypeRegistry:
    """Registry of all types in the SDK."""

    models: list[Model] = field(default_factory=list)
    enums: list[Enum] = field(default_factory=list)
    type_aliases: list[TypeAlias] = field(default_factory=list)


@dataclass
class Parameter:
    """Parameter definition for operations."""

    name: str
    python_name: str
    api_name: str
    location: Literal["query", "header", "path", "cookie", "body"]
    type: IRType
    description: str | None = None
    required: bool = False
    default: Any | None = None
    deprecated: bool = False
    examples: list[Any] = field(default_factory=list)


@dataclass
class EnvVar:
    """Environment variable mapping."""

    name: str
    maps_to: str
    required: bool = False
    description: str | None = None


@dataclass
class ClientProperty:
    """Client configuration property."""

    name: str
    type: IRType
    default: Any | None = None
    description: str | None = None


@dataclass
class UtilityMethod:
    """Client utility method (e.g., with_options, with_namespace)."""

    name: str
    description: str
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str = "Client"
    template: str = ""


@dataclass
class ClientMethod:
    """Client HTTP method."""

    name: str
    description: str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    return_type: IRType = field(default_factory=lambda: IRType(kind="any"))
    is_async: bool = True


@dataclass
class ClientConfig:
    """Client configuration."""

    name: str = "Client"
    init_params: list[Parameter] = field(default_factory=list)
    env_vars: list[EnvVar] = field(default_factory=list)
    properties: list[ClientProperty] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    utility_methods: list[UtilityMethod] = field(default_factory=list)


@dataclass
class PathParam:
    """Path parameter definition."""

    name: str
    python_name: str
    type: IRType
    description: str | None = None
    required: bool = True


@dataclass
class Encoding:
    """Encoding definition for multipart/form-data."""

    content_type: str | None = None
    headers: dict[str, Parameter] = field(default_factory=dict)
    style: str | None = None
    explode: bool = False


@dataclass
class ContentType:
    """Content type definition for request/response bodies."""

    mime_type: str
    schema: IRType | None = None
    encoding: dict[str, Encoding] | None = None
    examples: list[dict] = field(default_factory=list)


@dataclass
class RequestBody:
    """Request body definition."""

    description: str | None = None
    required: bool = False
    content_types: list[ContentType] = field(default_factory=list)


@dataclass
class Response:
    """Response definition."""

    status_code: str
    description: str | None = None
    content_types: list[ContentType] = field(default_factory=list)
    headers: dict[str, Parameter] = field(default_factory=dict)


@dataclass
class SecurityRequirement:
    """Security requirement for an operation."""

    scheme_name: str
    scopes: list[str] = field(default_factory=list)


@dataclass
class Operation:
    """API operation definition."""

    name: str
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    path: str
    operation_id: str | None = None
    description: str | None = None
    summary: str | None = None
    path_params: list[PathParam] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    query_params: list[Parameter] = field(default_factory=list)
    header_params: list[Parameter] = field(default_factory=list)
    cookie_params: list[Parameter] = field(default_factory=list)
    body_params: list[Parameter] = field(default_factory=list)
    request_body: RequestBody | None = None
    responses: list[Response] = field(default_factory=list)
    default_response: Response | None = None
    response_type: IRType | None = None
    return_format: Literal["json", "binary", "text", "stream", "multipart"] = "json"
    use_unpack_pattern: bool = False
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False
    security: list[SecurityRequirement] = field(default_factory=list)
    is_async: bool = True
    paginated: bool = False
    pagination_style: str | None = None


@dataclass
class NestedResource:
    """Nested resource definition (e.g., stages.instruct)."""

    name: str
    parent: str
    property_name: str
    description: str | None = None
    operations: list[Operation] = field(default_factory=list)
    detection_hint: str | None = None


@dataclass
class Resource:
    """API resource definition."""

    name: str
    description: str | None = None
    namespace: str | None = None
    tag: str | None = None
    path_prefix: str | None = None
    operations: list[Operation] = field(default_factory=list)
    nested_resources: list[NestedResource] = field(default_factory=list)
    requires_id: bool = False
    id_param_name: str | None = None


@dataclass
class FieldConversion:
    """Field conversion rule for converters."""

    from_name: str
    to_name: str
    transform: str | None = None
    conditional_omit: bool = False
    nested_convert: bool = False


@dataclass
class Converter:
    """snake_case to camelCase converter definition."""

    name: str
    input_type: str
    output_type: str = "dict"
    description: str | None = None
    conversions: list[FieldConversion] = field(default_factory=list)


@dataclass
class Helper:
    """Helper function definition."""

    name: str
    description: str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    return_type: IRType = field(default_factory=lambda: IRType(kind="any"))


@dataclass
class UtilityConfig:
    """Utility functions configuration."""

    converters: list[Converter] = field(default_factory=list)
    helpers: list[Helper] = field(default_factory=list)


@dataclass
class SDKProject:
    """Top-level IR representing entire SDK project."""

    metadata: ProjectMetadata
    auth: AuthConfig = field(default_factory=AuthConfig)
    namespaces: list[Namespace] = field(default_factory=list)
    types: TypeRegistry = field(default_factory=TypeRegistry)
    client: ClientConfig = field(default_factory=ClientConfig)
    resources: list[Resource] = field(default_factory=list)
    utilities: UtilityConfig = field(default_factory=UtilityConfig)
