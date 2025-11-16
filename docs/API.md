# API Reference

## CLI Commands

### `sdkgen generate`

Generate SDK from OpenAPI specification.

```bash
sdkgen generate [OPTIONS]
```

**Options:**

- `-i, --input TEXT` - Path or URL to OpenAPI specification (required)
- `-o, --output TEXT` - Output directory for generated SDK (required)
- `-l, --language TEXT` - Target language: python, typescript, go, rust (default: python)
- `-n, --package-name TEXT` - Package name (default: from OpenAPI title)

**Example:**

```bash
sdkgen generate \
  -i https://api.example.com/openapi.yaml \
  -o ./my-sdk \
  -l python \
  -n my_api_sdk
```

### `sdkgen validate`

Validate OpenAPI specification.

```bash
sdkgen validate -i SPEC_PATH
```

**Options:**

- `-i, --input TEXT` - Path or URL to OpenAPI specification (required)

**Example:**

```bash
sdkgen validate -i openapi.yaml
```

### `sdkgen show-ir`

Display intermediate representation of OpenAPI spec (for debugging).

```bash
sdkgen show-ir [OPTIONS]
```

**Options:**

- `-i, --input TEXT` - Path or URL to OpenAPI specification (required)
- `-o, --output TEXT` - Output file for IR JSON (optional)

**Example:**

```bash
# Print to console
sdkgen show-ir -i openapi.yaml

# Save to file
sdkgen show-ir -i openapi.yaml -o ir.json
```

## Generated SDK API (Python)

### Client

```python
from my_sdk import Client

client = Client(
    base_url: str = "",           # API base URL
    api_key: str = "",            # API key
    timeout: float = 600.0,       # Request timeout
    headers: dict = {}            # Custom headers
)
```

**Methods:**

- `client.request(method, path, **kwargs)` - Make HTTP request
- `client.request_raw(method, path, **kwargs)` - Return raw response
- `client.with_options(**kwargs)` - Create new client with updated options
- `client.with_namespace(prefix)` - Create client with URL prefix

### Resources

Generated resources are dataclasses with async methods.

```python
# List resources (GET array response)
results = await client.v1.users.list(
    page: int = 0,
    size: int = 100,
    **filters
)

# Get single resource (GET with ID)
user = await client.v1.users.get(user_id: str)

# Create resource (POST)
user = await client.v1.users.create(
    name: str,
    email: str,
    **optional_fields
)

# Update resource (PUT/PATCH)
user = await client.v1.users.update(
    user_id: str,
    **fields_to_update
)

# Delete resource (DELETE)
await client.v1.users.delete(user_id: str)
```

### Models

Models are TypedDict definitions:

```python
from my_sdk.models import User, CreateUserInput

# TypedDict for API responses
user: User = {
    "id": "123",
    "name": "John Doe",
    "email": "john@example.com"
}

# TypedDict for requests
create_data: CreateUserInput = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "age": 30  # Optional fields can be omitted
}

# Use with Unpack for type safety
user = await client.v1.users.create(**create_data)
```

### Enums

```python
from my_sdk.models import UserRole

role = UserRole.ADMIN
# or
role = "admin"  # String literal also works
```

### Namespaces

Generated SDKs support API versioning through namespaces:

```python
# V1 API
await client.v1.users.list()

# Beta API
await client.beta.features.list()

# Access namespace resources
v1 = client.v1  # Returns namespace with all v1 resources
```

## Core Classes

### IRBuilder

Orchestrates building IR from OpenAPI spec.

```python
from sdkgen.core.ir_builder import IRBuilder

builder = IRBuilder()
sdk_project = builder.build(spec, package_name="my_sdk")
```

### Parser

Parses and validates OpenAPI specifications.

```python
from sdkgen.core.parser import OpenAPIParser

parser = OpenAPIParser()
spec = await parser.parse("openapi.yaml")
```

### Analyzers

Pattern detection services:

```python
from sdkgen.analyzers.endpoint_analyzer import EndpointAnalyzer
from sdkgen.analyzers.namespace_analyzer import NamespaceAnalyzer

endpoint_analyzer = EndpointAnalyzer()
namespace_analyzer = NamespaceAnalyzer()
```

### Generators

Language-specific code generators:

```python
from sdkgen.generators.python.generator import PythonGenerator

generator = PythonGenerator()
generator.generate(sdk_project, output_dir)
```

## Environment Variables

Generated SDKs support environment variables for configuration:

- `BASE_URL` - API base URL
- `API_KEY` - API authentication key
- `{AUTH_SCHEME}_TOKEN` - For custom auth schemes

```bash
export BASE_URL="https://api.example.com"
export API_KEY="your-secret-key"
```

```python
# No need to pass credentials explicitly
client = Client()  # Reads from env vars
```
